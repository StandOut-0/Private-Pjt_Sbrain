from django.utils import timezone

from apps.execution.models import ExecutionEvent


TERMINAL_EVENTS = {
    'run.succeeded': ('프로젝트 작업 완료', 'success'),
    'run.failed': ('Agent 실행 오류', 'error'),
    'run.cancelled': ('프로젝트 작업 취소', 'artifact'),
}


def _relative_time(value):
    seconds = max(0, int((timezone.now() - value).total_seconds()))
    if seconds < 60:
        return '방금 전'
    if seconds < 3600:
        return f'{seconds // 60}분 전'
    if seconds < 86400:
        return f'{seconds // 3600}시간 전'
    return f'{seconds // 86400}일 전'


def get_user_notifications(account, limit=20):
    """Build the UI notification feed from persisted terminal run events."""
    if account is None:
        return []
    events = (ExecutionEvent.objects
              .filter(project__owner=account, event_type__in=TERMINAL_EVENTS)
              .select_related('project')
              .order_by('-created_at', '-id')[:limit])
    items = []
    for event in events:
        title, kind = TERMINAL_EVENTS[event.event_type]
        project_name = event.project.project_name
        message = f'{project_name} 프로젝트의 작업이 완료되었습니다.' if event.event_type == 'run.succeeded' else event.message
        if event.event_type == 'run.failed':
            message = f'{project_name} 프로젝트에서 실행 오류가 발생했습니다.'
        elif event.event_type == 'run.cancelled':
            message = f'{project_name} 프로젝트의 작업이 취소되었습니다.'
        items.append({
            'id': f'event-{event.pk}',
            'title': title,
            'message': message,
            'time': _relative_time(event.created_at),
            'type': kind,
            'url': f'/projects/{event.project_id}/',
        })
    return items
