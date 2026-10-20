from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
import re
from pathlib import Path

from apps import mockdata
from apps.accounts.session import get_user_account, login_required
from apps.projects.models import Project
from apps.projects.ownership import project_card_payload
from apps.projects.services import ProjectInputError, create_project
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
def project_detail(request, project_id=None):
    if project_id is None:
        # 관리자: 전체 프로젝트
        projects = mockdata.get_projects()

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

        context = {
            'project': project,
            'chat_guide': mockdata.CHAT_GUIDE,
            'chat_guides': _chat_guides(),
            'active_menu': 'projects',
            'active_project_id': project['id'],
        }

    return render_react(request, 'project-detail', context, active_menu='projects')


@login_required
def chat_reply(request, project_id):
    """Chatbot 임시 응답. Supervisor Agent 연동 전까지 되묻는 흐름만 재현한다."""
    message = request.POST.get('message', '').strip()
    if any(phrase in message for phrase in ('새 프로젝트', '프로젝트 생성', '프로젝트 만들어', '프로젝트 만들기')):
        match = re.search(r'(?:프로젝트(?:\s*이름)?\s*[:：]\s*)(.+)', message)
        return JsonResponse({
            'reply': '새 프로젝트 입력창을 열었습니다. 이름과 설명을 입력한 뒤 생성할 수 있어요.',
            'action': 'open_project_create',
            'title': match.group(1).strip() if match else '',
        })
    if not message:
        reply = '무엇을 도와드릴까요?'
    elif '기획' in message or '만들' in message:
        reply = '확인했습니다. Planning Agent로 요구사항을 정리할까요? 주요 고객층도 알려주세요.'
    else:
        reply = f'"{message}" 요청을 이렇게 진행할까요? Supervisor Agent가 작업을 분해합니다.'
    return JsonResponse({'reply': reply, 'agent': 'Supervisor'})
