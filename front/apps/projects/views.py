from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render

from apps import mockdata
from apps.accounts.session import login_required


@login_required
def project_list(request):
    context = {
        'projects': mockdata.get_projects(),
        'active_menu': 'projects',
    }
    return render(request, 'projects/list.html', context)

@login_required
def project_create(request):
    if request.method == 'POST':
        # Backend 연동 전까지는 생성 결과를 목록 화면으로만 반영한다.
        return redirect('projects:list')
    return render(request, 'projects/create.html', {'active_menu': 'projects'})


@login_required
def project_detail(request, project_id=None):
    if project_id is None:
        # 관리자: 전체 프로젝트
        projects = mockdata.get_projects()

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
            'active_menu': 'projects',
            'is_all_services': True,
        }

        return render(request, 'projects/detail.html', context)


    else:
        # 일반 사용자: 선택한 프로젝트 하나
        project = mockdata.get_project(project_id)

        if not project:
            raise Http404('project not found')

        context = {
            'project': project,
            'chat_guide': mockdata.CHAT_GUIDE,
            'active_menu': 'projects',
            'active_project_id': project['id'],
        }

    return render(request, 'projects/detail.html', context)


@login_required
def chat_reply(request, project_id):
    """Chatbot 임시 응답. Supervisor Agent 연동 전까지 되묻는 흐름만 재현한다."""
    message = request.POST.get('message', '').strip()
    if not message:
        reply = '무엇을 도와드릴까요?'
    elif '기획' in message or '만들' in message:
        reply = '확인했습니다. Planning Agent로 요구사항을 정리할까요? 주요 고객층도 알려주세요.'
    else:
        reply = f'"{message}" 요청을 이렇게 진행할까요? Supervisor Agent가 작업을 분해합니다.'
    return JsonResponse({'reply': reply, 'agent': 'Supervisor'})
