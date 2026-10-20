from django.shortcuts import render

from apps import mockdata
from apps.accounts.session import login_required


@login_required
def faq(request):
    return render(request, 'dashboard/faq.html', {'active_menu': 'faq'})


@login_required
def user_guide(request):
    return render(request, 'dashboard/user_guide.html', {'active_menu': 'user_guide'})


@login_required
def index(request):
    context = {
        'projects': mockdata.get_projects(),
        'tasks': mockdata.get_tasks(),
        'agent_executions': mockdata.get_agent_executions(),
        'artifacts': mockdata.get_recent_artifacts(),
        'active_menu': 'dashboard',
    }
    return render(request, 'dashboard/index.html', context)
