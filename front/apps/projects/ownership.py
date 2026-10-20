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
