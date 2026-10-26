from django.http import Http404
from django.utils import timezone

from apps.projects.models import Project


def get_owned_project(user_account, project_id):
    """Return only a project owned by this persisted account; hide other IDs."""
    if user_account is None:
        raise Http404('project not found')
    project = Project.objects.filter(pk=project_id, owner_id=user_account.pk).first()
    if project is None:
        raise Http404('project not found')
    return project


def project_payload(project):
    return {
        'id': project.pk,
        'title': project.project_name,
        'summary': project.description,
        'status': project.status,
        'created_at': project.created_at.isoformat().replace('+00:00', 'Z'),
        'updated_at': project.updated_at.isoformat().replace('+00:00', 'Z'),
    }


def project_card_payload(project):
    status = {
        Project.STATUS_ACTIVE: 'running',
        Project.STATUS_COMPLETED: 'done',
        Project.STATUS_ARCHIVED: 'ready',
    }.get(project.status, 'ready')
    from apps.execution.events import event_payload
    activities = [event_payload(event) for event in project.execution_events.all()[:30]]
    latest_run = project.runs.select_related('source_message').first()
    executions = list(latest_run.planning_task.executions.select_related('agent').all()) if latest_run and hasattr(latest_run, 'planning_task') else []
    execution_states = {execution.agent.key: execution.status for execution in executions}
    state_labels = {
        'queued': 'waiting', 'running': 'running', 'cancel_requested': 'running',
        'succeeded': 'done', 'failed': 'failed', 'cancelled': 'failed',
    }
    latest_state = state_labels.get(latest_run.status, 'waiting') if latest_run else 'waiting'
    completed = sum(execution.status in ('succeeded', 'failed', 'cancelled') for execution in executions)
    running = sum(execution.status in ('running', 'cancel_requested') for execution in executions)
    duration_values = [
        (run.finished_at - run.started_at).total_seconds()
        for run in project.runs.all() if run.started_at and run.finished_at
    ]
    return {
        **project_payload(project),
        'code': f'Project {project.pk:02d}',
        'status': status,
        'status_label': project.get_status_display(),
        'progress': 100 if latest_run and latest_run.status in ('succeeded', 'failed', 'cancelled') else (50 if latest_run and latest_run.status in ('running', 'cancel_requested') else (10 if latest_run else 0)),
        'stages': [{'name': 'planning', 'progress': 100 if latest_state in ('done', 'failed') else (50 if latest_state == 'running' else (10 if latest_run else 0))}],
        'pipeline_states': {
            'supervisor': 'waiting', 'task_queue': 'waiting',
            'planning': state_labels.get(execution_states.get('planning'), latest_state) if latest_run else 'waiting',
            'creative': 'waiting', 'engineering': 'waiting', 'data': 'waiting', 'ai': 'waiting', 'reflection': 'waiting',
        },
        'pipeline_running_count': running,
        'pipeline_done_count': completed,
        'last_run_label': timezone.localtime(latest_run.created_at).strftime('%Y-%m-%d %H:%M') if latest_run else '실행 이력 없음',
        'average_run_label': f'{sum(duration_values) / len(duration_values):.1f} sec' if duration_values else '미계측',
        'activities': activities,
        'latest_run_id': latest_run.pk if latest_run else None,
        'latest_run_status': latest_run.status if latest_run else None,
        'latest_run_source_message_id': latest_run.source_message_id if latest_run else None,
        'tree': [],
    }


def conversation_payload(conversation):
    return {
        'id': conversation.pk,
        'project_id': conversation.project_id,
        'title': conversation.title,
        'created_at': conversation.created_at.isoformat().replace('+00:00', 'Z'),
        'updated_at': conversation.updated_at.isoformat().replace('+00:00', 'Z'),
    }


def message_payload(message):
    return {
        'id': message.pk,
        'conversation_id': message.conversation_id,
        'role': message.role,
        'content': message.content,
        'created_at': message.created_at.isoformat().replace('+00:00', 'Z'),
    }
