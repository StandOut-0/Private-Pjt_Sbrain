from django.http import Http404
from django.shortcuts import render

from apps import mockdata
from apps.accounts.session import admin_required


@admin_required
def task_list(request):
    keyword = request.GET.get('q', '').strip()
    project = request.GET.get('project', '')
    status = request.GET.get('status', '')

    tasks = mockdata.get_tasks()
    if keyword:
        tasks = [task for task in tasks if keyword in task['name']]
    if project:
        tasks = [task for task in tasks if task['project'] == project]
    if status:
        tasks = [task for task in tasks if task['status'] == status]

    context = {
        'tasks': tasks,
        'projects': mockdata.get_projects(),
        'metrics': mockdata.TASK_METRICS,
        'trend': mockdata.TASK_TREND,
        'filters': {'q': keyword, 'project': project, 'status': status},
        'active_menu': 'tasks',
    }
    return render(request, 'management/tasks.html', context)


@admin_required
def agent_list(request):
    agents = mockdata.get_agents()
    context = {
        'supervisor': mockdata.get_agent('supervisor'),
        'workers': mockdata.get_worker_agents(),
        'running_count': len([
            agent for agent in agents
            if agent['group'] != 'engineering' and agent['status'] == 'running'
        ]),
        'total_count': len([agent for agent in agents if agent['group'] != 'engineering']),
        'active_menu': 'agents',
    }
    return render(request, 'management/agents.html', context)


@admin_required
def agent_detail(request, key):
    agent = mockdata.get_agent(key)
    if not agent:
        raise Http404('agent not found')
    context = {
        'agent': agent,
        'children': [mockdata.get_agent(child) for child in agent['children']],
        'active_menu': 'agents',
        'active_agent': key,
    }
    return render(request, 'management/agent_detail.html', context)


@admin_required
def results(request):
    project_id = request.GET.get('project', '')
    projects = mockdata.get_projects()
    selected = mockdata.get_project(project_id) if project_id else None
    if selected:
        tree = selected['tree']
    else:
        tree = [
            {'name': f"{project['title']} / {folder['name']}", 'files': folder['files']}
            for project in projects
            for folder in project['tree']
        ]
    context = {
        'projects': projects,
        'selected': selected,
        'tree': tree,
        'knowledge_stats': mockdata.KNOWLEDGE_STATS,
        'vector_documents': mockdata.VECTOR_DOCUMENTS,
        'search_metrics': mockdata.SEARCH_METRICS,
        'active_menu': 'results',
    }
    return render(request, 'management/results.html', context)
