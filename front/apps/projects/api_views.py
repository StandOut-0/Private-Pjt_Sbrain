import uuid

from django.http import Http404, JsonResponse
from django.views.decorators.http import require_GET

from apps.accounts.session import get_user_account
from apps.projects.ownership import get_owned_project, project_payload


def _error(status, code, message):
    return JsonResponse({
        'error': {
            'code': code,
            'message': message,
            'details': {},
            'request_id': f'req_{uuid.uuid4().hex[:16]}',
        },
    }, status=status)


@require_GET
def project_detail(request, project_id):
    account = get_user_account(request)
    if account is None:
        return _error(401, 'AUTH_REQUIRED', '로그인이 필요합니다.')

    try:
        project = get_owned_project(account, project_id)
    except Http404:
        return _error(404, 'PROJECT_NOT_FOUND', '프로젝트를 찾을 수 없습니다.')

    return JsonResponse(project_payload(project))
