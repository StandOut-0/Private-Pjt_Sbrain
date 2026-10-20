from apps import mockdata
from apps.accounts.session import login_required
from apps.react_pages import render_react


def _react_context(request):
    return {
        'projects': mockdata.get_projects(),
    }


@login_required
def faq(request):
    return render_react(request, 'faq', active_menu='faq')


@login_required
def notifications(request):
    return render_react(
        request,
        'notifications',
        {'notifications': mockdata.get_notifications()},
        active_menu='notifications',
    )


@login_required
def user_guide(request):
    return render_react(request, 'guide', active_menu='user_guide')


@login_required
def index(request):
    return render_react(request, 'dashboard', _react_context(request), active_menu='dashboard')
