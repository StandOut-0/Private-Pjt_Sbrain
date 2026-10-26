import json
import logging
import os

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.execution.models import Agent, AgentExecution, ProjectRun, Task
from apps.execution.supervisor import ensure_planning_task

logger = logging.getLogger(__name__)


class PlanningError(Exception):
    def __init__(self, code, public_message, *, retryable=False):
        super().__init__(public_message)
        self.code = code
        self.public_message = public_message
        self.retryable = retryable


class FakePlanningProvider:
    """Deterministic local provider used for repeatable MVP execution and tests."""

    def generate(self, request):
        requirements = request.get('known_requirements') or []
        functional_requirements = requirements or [
            '사용자가 요청한 목표를 달성하는 핵심 기능을 정의한다.',
        ]
        open_questions = [] if requirements else ['주요 사용자와 구체적인 기능 범위를 정한다.']
        objective = request['objective']
        return {
            'title': objective[:80],
            'summary': objective,
            'objective': objective,
            'target_users': [],
            'functional_requirements': functional_requirements,
            'user_flow': ['요청 접수', '요구사항 정리', '결과 검토'],
            'acceptance_criteria': [
                '정의한 요구사항을 사용자가 확인할 수 있다.',
                '필수 기능과 완료 조건이 서로 연결된다.',
            ],
            'assumptions': [],
            'open_questions': open_questions,
            'priority': 'normal',
            'provider': 'fake',
        }


def get_planning_provider():
    provider_name = os.environ.get('PLANNING_PROVIDER', 'fake').strip().casefold()
    if provider_name == 'fake':
        return FakePlanningProvider()
    if not settings.DEBUG:
        raise PlanningError(
            'PROVIDER_NOT_ALLOWED',
            '현재 환경에서 외부 Planning Provider를 사용할 수 없습니다.',
        )
    raise PlanningError(
        'PROVIDER_NOT_CONFIGURED',
        '선택한 Planning Provider가 설정되어 있지 않습니다.',
    )


def validate_prd(result):
    required = {
        'title', 'summary', 'objective', 'target_users', 'functional_requirements',
        'user_flow', 'acceptance_criteria', 'assumptions', 'open_questions', 'priority',
    }
    if not isinstance(result, dict) or required - set(result):
        raise PlanningError('INVALID_PROVIDER_OUTPUT', 'Planning 결과 형식이 올바르지 않습니다.')
    for key in ('title', 'summary', 'objective', 'priority'):
        if not isinstance(result[key], str):
            raise PlanningError('INVALID_PROVIDER_OUTPUT', 'Planning 결과 형식이 올바르지 않습니다.')
    for key in ('target_users', 'functional_requirements', 'user_flow', 'acceptance_criteria', 'assumptions', 'open_questions'):
        if not isinstance(result[key], list) or any(not isinstance(item, str) for item in result[key]):
            raise PlanningError('INVALID_PROVIDER_OUTPUT', 'Planning 결과 형식이 올바르지 않습니다.')
    if len(result['title']) > 200 or len(json.dumps(result, ensure_ascii=False)) > 100000:
        raise PlanningError('OUTPUT_TOO_LARGE', 'Planning 결과가 허용 크기를 초과했습니다.')
    return result


def process_run(run_id, provider=None):
    """Claim one queued run, call the provider outside the transaction, and persist its outcome."""
    with transaction.atomic():
        run = ProjectRun.objects.select_for_update().select_related(
            'project', 'source_message', 'conversation'
        ).filter(pk=run_id).first()
        if run is None:
            raise ProjectRun.DoesNotExist(run_id)
        if run.status != ProjectRun.STATUS_QUEUED:
            return run

        task = ensure_planning_task(run)
        if task.status != Task.STATUS_QUEUED:
            return run

        agent, _created = Agent.objects.get_or_create(
            key='planning',
            defaults={
                'name': 'Planning Agent',
                'group': 'planning',
                'description': '사용자 요청에서 PRD 초안을 작성합니다.',
            },
        )
        attempt_number = (task.executions.filter(agent=agent).order_by('-attempt_number').values_list('attempt_number', flat=True).first() or 0) + 1
        started_at = timezone.now()
        execution = AgentExecution.objects.create(
            task=task,
            agent=agent,
            input=json.dumps(run.instruction_snapshot, ensure_ascii=False),
            status=AgentExecution.STATUS_RUNNING,
            attempt_number=attempt_number,
            started_at=started_at,
        )
        run.status = ProjectRun.STATUS_RUNNING
        run.started_at = run.started_at or started_at
        run.save(update_fields=['status', 'started_at'])
        task.status = Task.STATUS_RUNNING
        task.started_at = task.started_at or started_at
        task.save(update_fields=['status', 'started_at', 'updated_at'])

    try:
        provider = provider or get_planning_provider()
        result = validate_prd(provider.generate(run.instruction_snapshot))
        outcome = (AgentExecution.STATUS_SUCCEEDED, '', '', json.dumps(result, ensure_ascii=False), False)
    except PlanningError as exc:
        outcome = (AgentExecution.STATUS_FAILED, exc.code, exc.public_message, '', exc.retryable)
    except Exception:
        logger.exception('Planning execution failed unexpectedly: run_id=%s execution_id=%s', run.pk, execution.pk)
        outcome = (
            AgentExecution.STATUS_FAILED,
            'INTERNAL_ERROR',
            '요청한 기획안을 생성하지 못했습니다. 잠시 뒤 다시 시도해주세요.',
            '',
            False,
        )

    finished_at = timezone.now()
    with transaction.atomic():
        execution.status, execution.error_code, execution.error_message, execution.output, execution.is_retryable = outcome
        execution.finished_at = finished_at
        execution.save(update_fields=['status', 'error_code', 'error_message', 'output', 'is_retryable', 'finished_at'])
        run = ProjectRun.objects.select_for_update().get(pk=run_id)
        task = Task.objects.select_for_update().get(pk=execution.task_id)
        is_success = execution.status == AgentExecution.STATUS_SUCCEEDED
        if is_success:
            from apps.execution.artifacts import persist_prd_artifact
            persist_prd_artifact(execution)
        terminal_status = ProjectRun.STATUS_SUCCEEDED if is_success else ProjectRun.STATUS_FAILED
        run.status = terminal_status
        run.finished_at = finished_at
        run.save(update_fields=['status', 'finished_at'])
        task.status = Task.STATUS_SUCCEEDED if is_success else Task.STATUS_FAILED
        task.finished_at = finished_at
        task.save(update_fields=['status', 'finished_at', 'updated_at'])
    return run
