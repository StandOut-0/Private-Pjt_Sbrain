from django.db import transaction

from apps.execution.models import Task


class SupervisorInputError(ValueError):
    pass


def structure_request(message_content):
    if not isinstance(message_content, str) or not message_content.strip():
        raise SupervisorInputError('실행할 사용자 요청이 없습니다.')

    goal = message_content.strip()
    if '로고' in goal:
        request_type = 'logo'
        task_title = '로고 프로젝트 요구사항 정리'
    elif '설문' in goal:
        request_type = 'survey'
        task_title = '설문 페이지 요구사항 정리'
    elif '원페이지' in goal or '랜딩' in goal:
        request_type = 'onepage'
        task_title = '원페이지 서비스 요구사항 정리'
    else:
        request_type = 'general'
        task_title = '프로젝트 요구사항 정리 및 PRD 작성'

    lines = [line.strip() for line in goal.splitlines() if line.strip()]
    return {
        'schema_version': 1,
        'request_type': request_type,
        'objective': lines[0][:500],
        'user_request': goal[:10000],
        'known_requirements': lines[1:21],
        'missing_information': [],
        'next_agent': 'planning',
        'expected_artifacts': ['prd.md'],
        'task_title': task_title,
    }


@transaction.atomic
def ensure_planning_task(run):
    snapshot = run.instruction_snapshot
    if not isinstance(snapshot, dict) or snapshot.get('schema_version') != 1:
        snapshot = structure_request(run.source_message.content)
        run.instruction_snapshot = snapshot
        run.save(update_fields=['instruction_snapshot'])

    task, _created = Task.objects.get_or_create(
        run=run,
        defaults={
            'project_id': run.project_id,
            'title': snapshot['task_title'],
            'description': snapshot['user_request'],
            'priority': 'normal',
            'status': Task.STATUS_QUEUED,
        },
    )
    return task
