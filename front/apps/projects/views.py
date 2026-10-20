from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
import re
from pathlib import Path

from apps import mockdata
from apps.accounts.session import get_user_account, login_required
from apps.projects.models import Project
from apps.projects.ownership import project_payload
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
    all_projects = mockdata.get_projects()
    keyword = request.GET.get('project_q', '').strip()
    status = request.GET.get('project_status', '').strip()
    valid_statuses = {project.get('status', '') for project in all_projects}
    if status not in valid_statuses:
        status = ''

    projects = all_projects
    if keyword:
        needle = keyword.casefold()
        projects = [
            project for project in projects
            if needle in ' '.join((project.get('code', ''), project.get('title', ''), project.get('summary', ''))).casefold()
        ]
    if status:
        projects = [project for project in projects if project.get('status') == status]

    context = {
        'projects': projects,
        'total_projects': len(all_projects),
        'project_statuses': sorted(valid_statuses),
        'filters': {'q': keyword, 'status': status},
        'active_menu': 'projects',
    }
    return render_react(request, 'project-list', context, active_menu='projects')

@login_required
def project_create(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            return redirect('projects:list')
        project = mockdata.create_project(
            title,
            request.POST.get('summary', ''),
            request.POST.get('goal', ''),
        )
        return redirect('projects:detail', project_id=project['id'])
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
        stored_project = Project.objects.filter(pk=project_id).first()
        if stored_project:
            account = get_user_account(request)
            if account is None or stored_project.owner_id != account.pk:
                raise Http404('project not found')
            project = {
                **project_payload(stored_project),
                'code': f'Project {stored_project.pk:02d}',
                'status_label': stored_project.get_status_display(),
                'progress': 0,
                'stages': [],
                'activities': [],
                'tree': [],
            }
        else:
            # 정적 예시 프로젝트는 사용자 데이터가 아닌 공용 Mock 데이터다.
            project = mockdata.get_project(project_id)

        if not project:
            raise Http404('project not found')

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
