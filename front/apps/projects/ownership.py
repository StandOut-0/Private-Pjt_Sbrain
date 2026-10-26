from django.http import Http404

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
    return {
        **project_payload(project),
        'code': f'Project {project.pk:02d}',
        'status': status,
        'status_label': project.get_status_display(),
        'progress': 0,
        'stages': [],
        'activities': [],
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
