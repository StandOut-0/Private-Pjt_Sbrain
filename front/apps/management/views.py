from django.http import Http404
from apps import mockdata
from apps.accounts.session import admin_required
from apps.react_pages import render_react
from apps.execution.models import Task
from apps.projects.models import Project
from datetime import timedelta
from django.utils import timezone


@admin_required
def task_list(request):
    keyword = request.GET.get('q', '').strip()
    project = request.GET.get('project', '')
    status = request.GET.get('status', '')

    queryset = Task.objects.select_related('project').prefetch_related('executions__agent').all()
    if keyword:
        queryset = queryset.filter(title__icontains=keyword)
    if project:
        queryset = queryset.filter(project__project_name=project)
    status_values = {'running': [Task.STATUS_RUNNING], 'done': [Task.STATUS_SUCCEEDED],
                     'failed': [Task.STATUS_FAILED, Task.STATUS_CANCELLED], 'waiting': [Task.STATUS_QUEUED, Task.STATUS_WAITING_FOR_USER]}
    if status in status_values:
        queryset = queryset.filter(status__in=status_values[status])
    all_tasks = list(Task.objects.all())
    task_rows = []
    for task in queryset[:200]:
        execution = task.executions.select_related('agent').first()
        state = {'queued': 'waiting', 'waiting_for_user': 'waiting', 'running': 'running',
                 'succeeded': 'done', 'failed': 'failed', 'cancelled': 'failed'}.get(task.status, 'waiting')
        elapsed = None
        if task.started_at and task.finished_at:
            elapsed = max(0, int((task.finished_at - task.started_at).total_seconds()))
        task_rows.append({
            'id': task.pk, 'started_at': (task.started_at or task.created_at).strftime('%Y-%m-%d %H:%M'),
            'agent': execution.agent.name if execution else 'Supervisor', 'name': task.title,
            'project': task.project.project_name, 'status': state,
            'status_label': {'waiting': '대기', 'running': '진행 중', 'done': '완료', 'failed': '실패'}[state],
            'duration': f'{elapsed} sec' if elapsed is not None else '미계측',
            'input_tokens': execution.input_tokens if execution else None,
            'output_tokens': execution.output_tokens if execution else None,
            'total_tokens': execution.input_tokens + execution.output_tokens if execution and execution.input_tokens is not None and execution.output_tokens is not None else None,
            'provider': execution.provider_name if execution else '미실행',
            'model': execution.model_name if execution else '미계측',
            'cost_usd': str(execution.estimated_cost_usd) if execution and execution.estimated_cost_usd is not None else None,
            'error_code': execution.error_code if execution else '',
        })

    completed = [task for task in all_tasks if task.status in (Task.STATUS_SUCCEEDED, Task.STATUS_FAILED, Task.STATUS_CANCELLED)]
    successes = sum(task.status == Task.STATUS_SUCCEEDED for task in completed)
    failures = sum(task.status in (Task.STATUS_FAILED, Task.STATUS_CANCELLED) for task in completed)
    durations = [(task.finished_at-task.started_at).total_seconds() for task in completed if task.started_at and task.finished_at]
    metrics = {
        'success_rate': f'{successes / len(completed) * 100:.1f}%' if completed else '—',
        'avg_duration': f'{sum(durations) / len(durations):.1f} sec' if durations else '미계측',
        'error_rate': f'{failures / len(completed) * 100:.1f}%' if completed else '—',
    }
    today = timezone.localdate()
    daily_labels = [(today-timedelta(days=6-i)).strftime('%m/%d') for i in range(7)]
    daily_values = [sum(task.created_at.date() == (today-timedelta(days=6-i)) for task in all_tasks) for i in range(7)]
    weekly_labels = [f'{3-i}주 전' if i < 3 else '이번 주' for i in range(4)]
    weekly_values = [sum((today-task.created_at.date()).days // 7 == (3-i) for task in all_tasks if task.created_at.date() <= today) for i in range(4)]

    context = {
        'tasks': task_rows,
        'projects': [{'id': project.pk, 'title': project.project_name} for project in Project.objects.order_by('project_name')],
        'metrics': metrics,
        'trend': {'daily': daily_values, 'daily_labels': daily_labels, 'weekly': weekly_values, 'weekly_labels': weekly_labels},
        'executions': task_rows,
        'filters': {'q': keyword, 'project': project, 'status': status},
        'active_menu': 'tasks',
    }
    return render_react(request, 'tasks', context, active_menu='tasks')


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
    return render_react(request, 'agents', context, active_menu='agents')


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
    return render_react(request, 'agent-detail', context, active_menu='agents')


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
        'statuses': sorted({document['status'] for document in mockdata.VECTOR_DOCUMENTS}),
    }
    return render_react(request, 'results', context, active_menu='results')
