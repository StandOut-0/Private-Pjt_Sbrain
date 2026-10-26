from apps.accounts.session import get_user_account, login_required
from apps.projects.models import Project
from apps.projects.ownership import project_card_payload
from apps.react_pages import render_react


def _react_context(request):
    account = get_user_account(request)
    return {
        'projects': [project_card_payload(project) for project in Project.objects.filter(owner=account)],
    }


@login_required
def faq(request):
    return render_react(request, 'faq', active_menu='faq')


@login_required
def notifications(request):
    return render_react(request, 'notifications', active_menu='notifications')


@login_required
def user_guide(request):
    return render_react(request, 'guide', active_menu='user_guide')


@login_required
def index(request):
    return render_react(request, 'dashboard', _react_context(request), active_menu='dashboard')
