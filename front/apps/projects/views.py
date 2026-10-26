from django.http import Http404, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
import json
import re
from pathlib import Path

from apps import mockdata
from apps.accounts.session import get_user_account, login_required
from apps.artifacts.models import Artifact
from apps.execution.models import ProjectRun
from apps.projects.models import Conversation, Project
from apps.reflection.models import ReflectionReport
from apps.projects.ownership import message_payload, project_card_payload
from apps.projects.services import ProjectInputError, append_message, create_conversation, create_project
from apps.react_pages import render_react


CHAT_GUIDE_FILES = {
    'guide': 'project-implementation.txt',
    'logo': 'logo-design.txt',
    'onepage': 'onepage-site.txt',
    'survey': 'survey-page.txt',
}


def _chat_guides():
    guide_root = Path(__file__).resolve().parents[2] / 'content' / 'project_guides'
    return {
        key: (guide_root / filename).read_text(encoding='utf-8')
        for key, filename in CHAT_GUIDE_FILES.items()
    }


def _artifact_tree(project):
    files = []
    for artifact in Artifact.objects.select_related('agent_execution__agent').filter(project=project):
        files.append({
            'id': artifact.pk,
            'name': f'{artifact.title}.json',
            'kind': 'text',
            'agent': artifact.agent_execution.agent.name,
            'size': f'{len(artifact.content.encode("utf-8")):,} bytes',
            'updated_at': timezone.localtime(artifact.created_at).strftime('%Y-%m-%d %H:%M'),
            'detail_url': f'/api/v1/projects/{project.pk}/artifacts/{artifact.pk}/',
            'download_url': f'/api/v1/projects/{project.pk}/artifacts/{artifact.pk}/download/',
        })
    return [{'name': project.project_name, 'files': files}] if files else []


@login_required
def project_list(request):
    account = get_user_account(request)
    queryset = Project.objects.filter(owner=account)
    keyword = request.GET.get('project_q', '').strip()
    status = request.GET.get('project_status', '').strip()
    status_to_model = {'running': Project.STATUS_ACTIVE, 'done': Project.STATUS_COMPLETED, 'ready': Project.STATUS_ARCHIVED}
    valid_statuses = set(status_to_model)
    if status not in valid_statuses:
        status = ''
    if keyword:
        queryset = queryset.filter(project_name__icontains=keyword) | queryset.filter(description__icontains=keyword)
    if status:
        queryset = queryset.filter(status=status_to_model[status])
    all_projects = Project.objects.filter(owner=account)
    projects = [project_card_payload(project) for project in queryset]

    context = {
        'projects': projects,
        'total_projects': all_projects.count(),
        'project_statuses': sorted(valid_statuses),
        'filters': {'q': keyword, 'status': status},
        'deleted': request.GET.get('deleted') == '1',
        'active_menu': 'projects',
    }
    return render_react(request, 'project-list', context, active_menu='projects')

@login_required
def project_create(request):
    if request.method == 'POST':
        try:
            project = create_project(
                owner=get_user_account(request),
                title=request.POST.get('title', ''),
                summary=request.POST.get('summary', ''),
                initial_message=request.POST.get('goal') or None,
            )
        except ProjectInputError:
            return JsonResponse({'error': '프로젝트 이름과 설명, 목표 길이를 확인해주세요.'}, status=422)
        return redirect('projects:detail', project_id=project.pk)
    # 생성 진입은 AppShell의 팝업에서 제공한다. 직접 주소를 열어도 빈 페이지는 보이지 않게 한다.
    return redirect('projects:list')


@login_required
def project_delete(request, project_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    account = get_user_account(request)
    project = Project.objects.filter(pk=project_id, owner=account).first()
    if project is None:
        raise Http404('project not found')
    active_runs = ProjectRun.objects.filter(
        project=project,
        status__in=[ProjectRun.STATUS_QUEUED, ProjectRun.STATUS_RUNNING, ProjectRun.STATUS_CANCEL_REQUESTED],
    )
    if active_runs.exists():
        return redirect(f"{reverse('projects:detail', args=[project.pk])}?delete_error=running")
    project.delete()
    return redirect(f"{reverse('projects:list')}?deleted=1")


@login_required
def project_detail(request, project_id=None):
    if project_id is None:
        # 관리자 can inspect all projects; regular users see only their own.
        account = get_user_account(request)
        project_query = Project.objects.all() if account.role == 'admin' else Project.objects.filter(owner=account)
        projects = []
        for stored_project in project_query:
            project_data = project_card_payload(stored_project)
            project_data['tree'] = _artifact_tree(stored_project)
            project_data['zip_url'] = f'/manage/results/download.zip?project={stored_project.pk}' if account.role == 'admin' else None
            projects.append(project_data)

        # 전체 서비스 진행률
        if projects:
            total_progress = round(
                sum(project.get('progress', 0) for project in projects)
                / len(projects)
            )
        else:
            total_progress = 0

        # 모든 프로젝트의 결과물을 하나의 트리로 통합
        project_tree = []

        for project in projects:
            project_tree.append({
                'name': project['title'],
                'type': 'folder',
                'children': project.get('tree', []),
            })

        context = {
            'projects': projects,
            'project_tree': project_tree,
            'total_progress': total_progress,
            'active_menu': 'projects',
            'is_all_services': True,
        }

        return render_react(request, 'project-all', context, active_menu='projects')


    else:
        # 일반 사용자: 선택한 프로젝트 하나
        account = get_user_account(request)
        stored_project = Project.objects.filter(pk=project_id, owner=account).first()
        if stored_project is None:
            raise Http404('project not found')
        project = project_card_payload(stored_project)
        project['artifacts'] = [
            {
                'id': artifact.pk,
                'title': artifact.title,
                'type': artifact.artifact_type,
                'logical_key': artifact.logical_key,
                'version': artifact.version,
                'description': artifact.description,
                'created_at': artifact.created_at.isoformat().replace('+00:00', 'Z'),
                'download_url': f'/api/v1/projects/{stored_project.pk}/artifacts/{artifact.pk}/download/',
                'reflection_url': f'/api/v1/projects/{stored_project.pk}/artifacts/{artifact.pk}/reflection/',
            }
            for artifact in stored_project.artifacts.all()
        ]
        latest_artifact = stored_project.artifacts.first()
        project['latest_reflection'] = None
        if latest_artifact:
            report = ReflectionReport.objects.filter(artifact=latest_artifact).first()
            if report:
                project['latest_reflection'] = {
                    'id': report.pk,
                    'artifact_id': report.artifact_id,
                    'total_score': report.total_score,
                    'summary': report.summary,
                    'score_details': report.score_details,
                    'improvements': report.improvements,
                    'is_mock': report.is_mock,
                }

        context = {
            'project': project,
            'chat_guide': mockdata.CHAT_GUIDE,
            'chat_guides': _chat_guides(),
            'delete_error': request.GET.get('delete_error') == 'running',
            'active_menu': 'projects',
            'active_project_id': project['id'],
        }

    return render_react(request, 'project-detail', context, active_menu='projects')


@login_required
def chat_reply(request, project_id):
    """Return an honest status message; conversational model responses are not wired yet."""
    if request.content_type == 'application/json':
        try:
            body = json.loads(request.body or '{}')
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': {'code': 'INVALID_JSON', 'message': '요청 본문은 올바른 JSON이어야 합니다.'}}, status=400)
        if not isinstance(body, dict):
            return JsonResponse({'error': {'code': 'INVALID_BODY', 'message': '요청 본문은 JSON 객체여야 합니다.'}}, status=400)
    else:
        body = request.POST

    message_value = body.get('message', '')
    if not isinstance(message_value, str) or not message_value.strip() or len(message_value.strip()) > 10000:
        return JsonResponse({'error': {'code': 'VALIDATION_ERROR', 'message': '메시지는 1자 이상 10,000자 이하여야 합니다.'}}, status=422)

    account = get_user_account(request)
    project = Project.objects.filter(pk=project_id, owner=account).first()
    if project is None:
        return JsonResponse({'error': {'code': 'PROJECT_NOT_FOUND', 'message': '프로젝트를 찾을 수 없습니다.'}}, status=404)
    try:
        conversation_id = int(body.get('conversation_id')) if body.get('conversation_id') else None
    except (TypeError, ValueError):
        return JsonResponse({'error': {'code': 'VALIDATION_ERROR', 'message': '대화 정보가 올바르지 않습니다.'}}, status=422)
    conversation = (
        Conversation.objects.filter(pk=conversation_id, project=project, owner=account).first()
        if conversation_id else Conversation.objects.filter(project=project, owner=account).first()
    )
    if conversation is None and conversation_id:
        return JsonResponse({'error': {'code': 'CONVERSATION_NOT_FOUND', 'message': '대화를 찾을 수 없습니다.'}}, status=404)
    if conversation is None:
        conversation = create_conversation(project=project, owner=account)

    message = message_value.strip()
    if not conversation_id and message:
        append_message(conversation=conversation, content=message, role='user')
    if any(phrase in message for phrase in ('새 프로젝트', '프로젝트 생성', '프로젝트 만들어', '프로젝트 만들기')):
        match = re.search(r'(?:프로젝트(?:\s*이름)?\s*[:：]\s*)(.+)', message)
        reply = '새 프로젝트 입력창을 열었습니다. 이름과 설명을 입력한 뒤 생성할 수 있어요.'
        title = match.group(1).strip() if match else ''
        action = 'open_project_create'
    elif not message:
        reply = '무엇을 도와드릴까요?'
        title = ''
        action = ''
    else:
        run = ProjectRun.objects.filter(
            project=project,
            conversation=conversation,
            source_message__content=message,
        ).order_by('-created_at').first()
        if run:
            reply = '요청을 대화에 저장하고 Planning Agent 실행을 요청했습니다. 처리 결과는 프로젝트 결과물과 실행 이력에서 확인할 수 있습니다.'
        else:
            reply = '메시지를 저장했습니다. 대화형 AI 답변은 아직 연결되지 않았습니다.'
        title = ''
        action = ''

    assistant_message = append_message(
        conversation=conversation,
        content=reply,
        role='assistant',
    )
    return JsonResponse({
            'reply': reply,
            'agent': 'Supervisor',
            'action': action,
            'title': title,
            'assistant_message': message_payload(assistant_message),
        })
