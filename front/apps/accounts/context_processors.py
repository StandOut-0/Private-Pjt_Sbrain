from apps import mockdata
from apps.accounts.session import get_user


def current_user(request):
    return {
        'sb_user': get_user(request),
        'nav_projects': mockdata.get_projects(),
    }
