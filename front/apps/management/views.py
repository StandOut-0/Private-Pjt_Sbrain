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
    keyword = request.GET.get('q', '').strip()
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
    if keyword:
        tree = [dict(folder, files=[file for file in folder['files']
                                  if keyword.casefold() in file['name'].casefold()])
                for folder in tree]
        tree = [folder for folder in tree if folder['files']]
    rag_query = request.GET.get('rag_q', '').strip()
    rag_project = request.GET.get('rag_project', '')
    rag_status = request.GET.get('rag_status', '')
    vector_documents = [document for document in mockdata.VECTOR_DOCUMENTS
                        if (not rag_query or rag_query.casefold() in document['document'].casefold())
                        and (not rag_project or document['project'] == rag_project)
                        and (not rag_status or document['status'] == rag_status)]
    context = {
        'projects': projects,
        'selected': selected,
        'results_tab': 'knowledge' if request.GET.get('tab') == 'knowledge' else 'files',
        'rag_filters': {'q': rag_query, 'project': rag_project, 'status': rag_status},
        'rag_statuses': sorted({document['status'] for document in mockdata.VECTOR_DOCUMENTS}),
        'keyword': keyword,
        'tree': tree,
        'knowledge_stats': mockdata.KNOWLEDGE_STATS,
        'vector_documents': vector_documents,
        'search_metrics': mockdata.SEARCH_METRICS,
        'active_menu': 'results',
    }
    return render(request, 'management/results.html', context)
