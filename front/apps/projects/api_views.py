import json
import uuid
import base64
import binascii
from datetime import datetime

from django.db.models import Q
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_http_methods

from apps.accounts.session import get_user_account
from apps.projects.models import Project
from apps.projects.ownership import get_owned_project, project_card_payload, project_payload
from apps.projects.services import ProjectInputError, create_project, update_project


def _error(status, code, message):
    return JsonResponse({
        'error': {
            'code': code,
            'message': message,
            'details': {},
            'request_id': f'req_{uuid.uuid4().hex[:16]}',
        },
    }, status=status)


def _authenticated_account(request):
    account = get_user_account(request)
    if account is None:
        return None, _error(401, 'AUTH_REQUIRED', '로그인이 필요합니다.')
    return account, None


@require_http_methods(['GET', 'POST'])
def project_collection(request):
    account, error = _authenticated_account(request)
    if error:
        return error

    if request.method == 'GET':
        queryset = Project.objects.filter(owner=account)
        query = request.GET.get('query', '').strip()
        status = request.GET.get('status', '').strip()
        if query:
            queryset = queryset.filter(Q(project_name__icontains=query) | Q(description__icontains=query))
        if status:
            if status not in {value for value, _label in Project.STATUS_CHOICES}:
                return _error(422, 'VALIDATION_ERROR', '지원하지 않는 프로젝트 상태입니다.')
            queryset = queryset.filter(status=status)
        limit = min(max(int(request.GET.get('limit', 20)) if request.GET.get('limit', '20').isdigit() else 20, 1), 100)
        cursor = request.GET.get('cursor')
        if cursor:
            try:
                decoded = json.loads(base64.urlsafe_b64decode(cursor + '=' * (-len(cursor) % 4)))
                cursor_updated = datetime.fromisoformat(decoded['updated_at'].replace('Z', '+00:00'))
                cursor_id = int(decoded['id'])
            except (ValueError, KeyError, TypeError, json.JSONDecodeError, binascii.Error):
                return _error(422, 'VALIDATION_ERROR', '목록 cursor가 올바르지 않습니다.')
            queryset = queryset.filter(Q(updated_at__lt=cursor_updated) | Q(updated_at=cursor_updated, id__lt=cursor_id))
        projects = list(queryset[:limit + 1])
        has_more = len(projects) > limit
        projects = projects[:limit]
        last = projects[-1] if has_more and projects else None
        next_cursor = None
        if last:
            cursor_json = json.dumps({'updated_at': last.updated_at.isoformat().replace('+00:00', 'Z'), 'id': last.pk}, separators=(',', ':'))
            next_cursor = base64.urlsafe_b64encode(cursor_json.encode()).decode().rstrip('=')
        return JsonResponse({
            'items': [project_payload(project) for project in projects],
            'next_cursor': next_cursor,
        })

    try:
        body = json.loads(request.body or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error(400, 'INVALID_JSON', '요청 본문은 올바른 JSON이어야 합니다.')
    if not isinstance(body, dict):
        return _error(400, 'INVALID_BODY', '프로젝트 정보 객체가 필요합니다.')
    if any(key in body and not isinstance(body[key], str) for key in ('title', 'summary', 'initial_message')):
        return _error(422, 'VALIDATION_ERROR', '프로젝트 필드 값은 문자열이어야 합니다.')
    try:
        project = create_project(
            owner=account,
            title=str(body.get('title', '')),
            summary=str(body.get('summary', '')),
            initial_message=str(body['initial_message']) if 'initial_message' in body else None,
        )
    except ProjectInputError as exc:
        return _error(422, 'VALIDATION_ERROR', str(exc))
    payload = project_payload(project)
    conversation = project.conversations.first()
    message = conversation.messages.first() if conversation else None
    return JsonResponse({
        'project': payload,
        'conversation': ({'id': conversation.pk, 'title': conversation.title} if conversation else None),
        'initial_message': ({
            'id': message.pk,
            'role': message.role,
            'content': message.content,
            'created_at': message.created_at.isoformat().replace('+00:00', 'Z'),
        } if message else None),
    }, status=201)


@require_http_methods(['GET', 'PATCH'])
def project_detail(request, project_id):
    account, error = _authenticated_account(request)
    if error:
        return error

    try:
        project = get_owned_project(account, project_id)
    except Http404:
        return _error(404, 'PROJECT_NOT_FOUND', '프로젝트를 찾을 수 없습니다.')

    if request.method == 'PATCH':
        try:
            body = json.loads(request.body or '{}')
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _error(400, 'INVALID_JSON', '요청 본문은 올바른 JSON이어야 합니다.')
        if not isinstance(body, dict) or not body or set(body) - {'title', 'summary', 'status'}:
            return _error(422, 'VALIDATION_ERROR', '수정할 수 있는 프로젝트 필드(title, summary, status)를 확인해주세요.')
        try:
            project = update_project(project, **body)
        except ProjectInputError as exc:
            return _error(422, 'VALIDATION_ERROR', str(exc))

    return JsonResponse(project_payload(project))
