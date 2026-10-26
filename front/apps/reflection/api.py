import json
import uuid

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from apps.accounts.models import UserAccount
from apps.accounts.session import get_user_account
from apps.reflection.models import QualityCriterion
from apps.artifacts.models import Artifact
from apps.projects.models import Project
from apps.reflection.evaluator import evaluate_artifact


def _error(status, code, message):
    return JsonResponse({'error': {'code': code, 'message': message, 'details': {}, 'request_id': f'req_{uuid.uuid4().hex[:16]}'}}, status=status)


def _snapshot():
    return [{'key': item.key, 'label': item.label, 'description': item.description, 'weight': item.weight}
            for item in QualityCriterion.objects.filter(is_active=True)]


@require_GET
def criteria(request):
    if get_user_account(request) is None:
        return _error(401, 'AUTH_REQUIRED', '로그인이 필요합니다.')
    active = _snapshot()
    return JsonResponse({'items': active, 'total_weight': sum(item['weight'] for item in active)})


@require_POST
def replace_criteria(request):
    account = get_user_account(request)
    if account is None:
        return _error(401, 'AUTH_REQUIRED', '로그인이 필요합니다.')
    if account.role != UserAccount.ROLE_ADMIN:
        return _error(403, 'ADMIN_REQUIRED', '관리자만 평가 기준을 변경할 수 있습니다.')
    try:
        body = json.loads(request.body or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error(400, 'INVALID_JSON', '요청 본문은 올바른 JSON이어야 합니다.')
    items = body.get('items') if isinstance(body, dict) else None
    if not isinstance(items, list) or not items:
        return _error(422, 'VALIDATION_ERROR', 'items 배열이 필요합니다.')
    keys = set()
    total = 0
    for item in items:
        if not isinstance(item, dict) or set(item) != {'key', 'label', 'description', 'weight', 'is_active', 'sort_order'}:
            return _error(422, 'VALIDATION_ERROR', '평가 기준 항목 형식이 올바르지 않습니다.')
        if not isinstance(item['key'], str) or not item['key'] or item['key'] in keys:
            return _error(422, 'VALIDATION_ERROR', '평가 기준 key는 중복 없이 입력해야 합니다.')
        if not isinstance(item['weight'], int) or isinstance(item['weight'], bool) or not 0 <= item['weight'] <= 100:
            return _error(422, 'VALIDATION_ERROR', '가중치는 0에서 100 사이 정수여야 합니다.')
        if not isinstance(item['is_active'], bool) or not isinstance(item['label'], str) or not isinstance(item['description'], str):
            return _error(422, 'VALIDATION_ERROR', '평가 기준 값 형식이 올바르지 않습니다.')
        keys.add(item['key'])
        if item['is_active']:
            total += item['weight']
    if total != 100:
        return _error(422, 'WEIGHT_SUM_INVALID', '활성 평가 기준의 가중치 합계는 100이어야 합니다.')
    with transaction.atomic():
        QualityCriterion.objects.all().delete()
        QualityCriterion.objects.bulk_create([
            QualityCriterion(key=item['key'], label=item['label'][:120], description=item['description'][:300],
                             weight=item['weight'], is_active=item['is_active'], sort_order=item['sort_order'])
            for item in items
        ])
    return JsonResponse({'items': _snapshot(), 'total_weight': 100})


def _report_payload(report):
    return {'id': report.pk, 'artifact_id': report.artifact_id, 'run_id': report.run_id,
            'criteria_snapshot': report.criteria_snapshot, 'score_details': report.score_details,
            'total_score': report.total_score, 'summary': report.summary,
            'improvements': report.improvements, 'is_mock': report.is_mock,
            'evaluation_label': '개발용 mock 평가' if report.is_mock else '실제 평가',
            'created_at': report.created_at.isoformat().replace('+00:00', 'Z')}


@require_http_methods(['GET', 'POST'])
def artifact_reflection(request, project_id, artifact_id):
    account = get_user_account(request)
    if account is None:
        return _error(401, 'AUTH_REQUIRED', '로그인이 필요합니다.')
    project = Project.objects.filter(pk=project_id, owner=account).first()
    if project is None:
        return _error(404, 'PROJECT_NOT_FOUND', '프로젝트를 찾을 수 없습니다.')
    artifact = Artifact.objects.filter(pk=artifact_id, project=project).first()
    if artifact is None:
        return _error(404, 'ARTIFACT_NOT_FOUND', '결과물을 찾을 수 없습니다.')
    if request.method == 'GET':
        report = getattr(artifact, 'reflection_report', None)
        if report is None:
            return _error(404, 'REFLECTION_NOT_FOUND', '평가 기록이 없습니다.')
        return JsonResponse(_report_payload(report))
    try:
        report, created = evaluate_artifact(artifact)
    except ValueError:
        return _error(409, 'CRITERIA_NOT_READY', '활성 평가 기준의 가중치를 확인해주세요.')
    return JsonResponse(_report_payload(report), status=201 if created else 200)
