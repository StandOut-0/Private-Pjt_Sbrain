import uuid

from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET

from apps.accounts.session import get_user_account
from apps.artifacts.models import Artifact
from apps.projects.models import Project


def _error(status, code, message):
    return JsonResponse({'error': {'code': code, 'message': message, 'details': {}, 'request_id': f'req_{uuid.uuid4().hex[:16]}'}}, status=status)


def _payload(artifact):
    return {'id': artifact.pk, 'project_id': artifact.project_id, 'task_id': artifact.task_id,
            'agent_execution_id': artifact.agent_execution_id, 'type': artifact.artifact_type,
            'title': artifact.title, 'description': artifact.description, 'logical_key': artifact.logical_key,
            'version': artifact.version, 'mime_type': artifact.mime_type,
            'created_at': artifact.created_at.isoformat().replace('+00:00', 'Z'),
            'detail_url': f'/api/v1/projects/{artifact.project_id}/artifacts/{artifact.pk}/',
            'download_url': f'/api/v1/projects/{artifact.project_id}/artifacts/{artifact.pk}/download/'}


def _authorized(request, project_id):
    account = get_user_account(request)
    if account is None:
        return None, _error(401, 'AUTH_REQUIRED', '로그인이 필요합니다.')
    project = Project.objects.filter(pk=project_id, owner=account).first()
    if project is None:
        return None, _error(404, 'PROJECT_NOT_FOUND', '프로젝트를 찾을 수 없습니다.')
    return project, None


@require_GET
def artifact_collection(request, project_id):
    project, error = _authorized(request, project_id)
    if error:
        return error
    return JsonResponse({'items': [_payload(item) for item in project.artifacts.all()]})


@require_GET
def artifact_detail(request, project_id, artifact_id):
    project, error = _authorized(request, project_id)
    if error:
        return error
    artifact = Artifact.objects.filter(pk=artifact_id, project=project).first()
    if artifact is None:
        return _error(404, 'ARTIFACT_NOT_FOUND', '결과물을 찾을 수 없습니다.')
    return JsonResponse({**_payload(artifact), 'content': artifact.content})


@require_GET
def artifact_download(request, project_id, artifact_id):
    project, error = _authorized(request, project_id)
    if error:
        return error
    artifact = Artifact.objects.filter(pk=artifact_id, project=project).first()
    if artifact is None:
        return _error(404, 'ARTIFACT_NOT_FOUND', '결과물을 찾을 수 없습니다.')
    response = HttpResponse(artifact.content, content_type=artifact.mime_type)
    response['Content-Disposition'] = f'attachment; filename="artifact-{artifact.pk}-v{artifact.version}.json"'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
