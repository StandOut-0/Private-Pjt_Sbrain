import json
import uuid

from django.db import IntegrityError, transaction
from django.http import Http404, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from apps.accounts.session import get_user_account
from apps.execution.models import AgentExecution, ProjectRun, Task
from apps.execution.supervisor import ensure_planning_task
from apps.execution.events import record_event
from apps.projects.models import Conversation, Message, Project


def _error(status, code, message):
    return JsonResponse({
        'error': {
            'code': code,
            'message': message,
            'details': {},
            'request_id': f'req_{uuid.uuid4().hex[:16]}',
        },
    }, status=status)


def _run_payload(run):
    try:
        task = run.planning_task
    except Task.DoesNotExist:
        task = None
    latest_execution = None
    if task:
        latest_execution = task.executions.first()
    return {
        'id': run.pk,
        'project_id': run.project_id,
        'conversation_id': run.conversation_id,
        'source_message_id': run.source_message_id,
        'previous_run_id': run.previous_run_id,
        'retry_count': run.retry_count,
        'status': run.status,
        'progress': 0,
        'created_at': run.created_at.isoformat().replace('+00:00', 'Z'),
        'started_at': run.started_at.isoformat().replace('+00:00', 'Z') if run.started_at else None,
        'finished_at': run.finished_at.isoformat().replace('+00:00', 'Z') if run.finished_at else None,
        'task': ({'id': task.pk, 'title': task.title, 'status': task.status} if task else None),
        'failure': ({'code': latest_execution.error_code, 'message': latest_execution.error_message,
                     'retryable': latest_execution.is_retryable}
                    if latest_execution and latest_execution.status == AgentExecution.STATUS_FAILED else None),
    }


def _parse_json(request):
    try:
        body = json.loads(request.body or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, _error(400, 'INVALID_JSON', '요청 본문은 올바른 JSON이어야 합니다.')
    if not isinstance(body, dict):
        return None, _error(400, 'INVALID_BODY', '요청 본문은 JSON 객체여야 합니다.')
    return body, None


@require_POST
def create_run(request, project_id):
    account = get_user_account(request)
    if account is None:
        return _error(401, 'AUTH_REQUIRED', '로그인이 필요합니다.')
    project = Project.objects.filter(pk=project_id, owner=account).first()
    if project is None:
        return _error(404, 'PROJECT_NOT_FOUND', '프로젝트를 찾을 수 없습니다.')

    raw_key = request.headers.get('Idempotency-Key', '').strip()
    try:
        idempotency_key = str(uuid.UUID(raw_key))
    except (ValueError, AttributeError):
        return _error(422, 'VALIDATION_ERROR', 'Idempotency-Key에 UUID가 필요합니다.')

    body, error = _parse_json(request)
    if error:
        return error
    allowed = {'conversation_id', 'source_message_id', 'previous_run_id', 'feedback'}
    if set(body) - allowed or 'conversation_id' not in body or 'source_message_id' not in body:
        return _error(422, 'VALIDATION_ERROR', 'conversation_id와 source_message_id가 필요합니다.')
    if 'feedback' in body and (not isinstance(body['feedback'], str) or len(body['feedback']) > 10000):
        return _error(422, 'VALIDATION_ERROR', 'feedback는 10,000자 이하 문자열이어야 합니다.')
    try:
        ids = [body['conversation_id'], body['source_message_id']]
        if body.get('previous_run_id') is not None:
            ids.append(body['previous_run_id'])
        if any(isinstance(value, bool) for value in ids):
            raise ValueError('boolean ID')
        conversation_id = int(body['conversation_id'])
        source_message_id = int(body['source_message_id'])
        previous_run_id = int(body['previous_run_id']) if body.get('previous_run_id') is not None else None
    except (TypeError, ValueError):
        return _error(422, 'VALIDATION_ERROR', '실행 참조 ID가 올바르지 않습니다.')

    conversation = Conversation.objects.filter(
        pk=conversation_id,
        project=project,
        owner=account,
        project__owner=account,
    ).first()
    if conversation is None:
        return _error(404, 'CONVERSATION_NOT_FOUND', '대화를 찾을 수 없습니다.')
    source_message = Message.objects.filter(
        pk=source_message_id,
        conversation=conversation,
        role=Message.ROLE_USER,
    ).first()
    if source_message is None:
        return _error(404, 'MESSAGE_NOT_FOUND', '요청 메시지를 찾을 수 없습니다.')

    previous_run = None
    if previous_run_id is not None:
        previous_run = ProjectRun.objects.filter(pk=previous_run_id, project=project).first()
        if previous_run is None:
            return _error(404, 'RUN_NOT_FOUND', '이전 실행을 찾을 수 없습니다.')

    existing = ProjectRun.objects.filter(project=project, idempotency_key=idempotency_key).first()
    if existing:
        if existing.source_message_id != source_message.pk:
            return _error(409, 'IDEMPOTENCY_KEY_REUSED', '같은 요청 키가 다른 메시지에 이미 사용됐습니다.')
        ensure_planning_task(existing)
        return JsonResponse(_run_payload(existing), status=200)

    try:
        with transaction.atomic():
            run = ProjectRun.objects.create(
                project=project,
                requested_by=account,
                conversation=conversation,
                source_message=source_message,
                previous_run=previous_run,
                idempotency_key=idempotency_key,
                feedback=body.get('feedback', '').strip(),
                status=ProjectRun.STATUS_QUEUED,
            )
            ensure_planning_task(run)
            record_event(project=project, run=run, task=run.planning_task, event_type='run.queued',
                         message='프로젝트 실행이 대기열에 등록되었습니다.', to_status=run.status)
    except IntegrityError:
        existing = ProjectRun.objects.filter(project=project, idempotency_key=idempotency_key).first()
        if existing and existing.source_message_id == source_message.pk:
            ensure_planning_task(existing)
            return JsonResponse(_run_payload(existing), status=200)
        if existing:
            return _error(409, 'IDEMPOTENCY_KEY_REUSED', '같은 요청 키가 다른 메시지에 이미 사용됐습니다.')
        raise

    response = JsonResponse(_run_payload(run), status=202)
    response['Location'] = reverse('project_api:run_detail', args=[project.pk, run.pk])
    return response


@require_GET
def run_detail(request, project_id, run_id):
    account = get_user_account(request)
    if account is None:
        return _error(401, 'AUTH_REQUIRED', '로그인이 필요합니다.')
    if not Project.objects.filter(pk=project_id, owner=account).exists():
        return _error(404, 'PROJECT_NOT_FOUND', '프로젝트를 찾을 수 없습니다.')
    run = ProjectRun.objects.filter(pk=run_id, project_id=project_id).first()
    if run is None:
        return _error(404, 'RUN_NOT_FOUND', '실행을 찾을 수 없습니다.')
    ensure_planning_task(run)
    return JsonResponse(_run_payload(run))


@require_GET
def project_events(request, project_id):
    account = get_user_account(request)
    if account is None:
        return _error(401, 'AUTH_REQUIRED', '로그인이 필요합니다.')
    project = Project.objects.filter(pk=project_id, owner=account).first()
    if project is None:
        return _error(404, 'PROJECT_NOT_FOUND', '프로젝트를 찾을 수 없습니다.')
    from apps.execution.events import event_payload
    events = project.execution_events.select_related('run', 'task', 'execution')[:100]
    return JsonResponse({'items': [event_payload(event) for event in events]})


@require_POST
def retry_run(request, project_id, run_id):
    account = get_user_account(request)
    if account is None:
        return _error(401, 'AUTH_REQUIRED', '로그인이 필요합니다.')
    project = Project.objects.filter(pk=project_id, owner=account).first()
    if project is None:
        return _error(404, 'PROJECT_NOT_FOUND', '프로젝트를 찾을 수 없습니다.')
    failed_run = ProjectRun.objects.filter(pk=run_id, project=project).select_related('conversation', 'source_message').first()
    if failed_run is None:
        return _error(404, 'RUN_NOT_FOUND', '실행을 찾을 수 없습니다.')
    if failed_run.status != ProjectRun.STATUS_FAILED:
        return _error(409, 'RUN_NOT_RETRYABLE', '실패한 실행만 재시도할 수 있습니다.')
    task = getattr(failed_run, 'planning_task', None)
    execution = task.executions.first() if task else None
    if not execution or not execution.is_retryable:
        return _error(409, 'FAILURE_NOT_RETRYABLE', '이 실패는 자동 재시도할 수 없습니다.')
    if failed_run.retry_count >= 3:
        return _error(409, 'RETRY_LIMIT_REACHED', '재시도 횟수 3회를 초과할 수 없습니다.')
    try:
        key = str(uuid.UUID(request.headers.get('Idempotency-Key', '').strip()))
    except (ValueError, AttributeError):
        return _error(422, 'VALIDATION_ERROR', 'Idempotency-Key에 UUID가 필요합니다.')
    existing = ProjectRun.objects.filter(project=project, idempotency_key=key).first()
    if existing:
        if existing.previous_run_id == failed_run.pk:
            return JsonResponse(_run_payload(existing), status=200)
        return _error(409, 'IDEMPOTENCY_KEY_REUSED', '같은 요청 키가 다른 재시도에 이미 사용됐습니다.')
    with transaction.atomic():
        new_run = ProjectRun.objects.create(
            project=project, requested_by=account, conversation=failed_run.conversation,
            source_message=failed_run.source_message, previous_run=failed_run,
            idempotency_key=key, status=ProjectRun.STATUS_QUEUED,
            feedback=failed_run.feedback, instruction_snapshot=failed_run.instruction_snapshot,
            retry_count=failed_run.retry_count + 1,
        )
        new_task = ensure_planning_task(new_run)
        record_event(project=project, run=new_run, task=new_task, event_type='run.retry_queued',
                     message=f'실패 지점에서 재시도 {new_run.retry_count}/3회를 대기열에 등록했습니다.',
                     from_status=failed_run.status, to_status=new_run.status,
                     metadata={'previous_run_id': failed_run.pk, 'retry_count': new_run.retry_count})
    response = JsonResponse(_run_payload(new_run), status=202)
    response['Location'] = reverse('project_api:run_detail', args=[project.pk, new_run.pk])
    return response
