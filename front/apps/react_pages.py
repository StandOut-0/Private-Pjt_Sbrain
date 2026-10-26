import json
from pathlib import Path

from django.conf import settings
from django.shortcuts import render
from django.templatetags.static import static

from apps import mockdata
from apps.accounts.session import get_user
from apps.accounts.session import get_user_account
from apps.dashboard.notifications import get_user_notifications
from apps.projects.models import Project
from apps.projects.ownership import project_card_payload

PAGE_STYLES = {
    'dashboard': ['dashboard'], 'faq': ['faq'], 'guide': ['comingsoon', 'user-guide'], 'agents': ['agents'],
    'agent-detail': ['agents'], 'results': ['results'], 'tasks': ['tasks'],
    'project-list': [], 'project-detail': [], 'project-all': [], 'project-create': [],
    'comingsoon-list': ['comingsoon'], 'comingsoon-detail': ['comingsoon-detail'],
    'comingsoon-manage': ['comingsoon-management'], 'comingsoon-editor': ['comingsoon-management'],
    'notifications': [],
}

PAGE_SCRIPTS = {
    'project-detail': ['artifact_browser.js', 'chat.js'],
    'project-all': ['artifact_browser.js'],
    'results': ['artifact_browser.js'],
}


def render_react(request, page, data=None, *, shell=True, status=200, active_menu=''):
    manifest_path = Path(settings.BASE_DIR) / 'static' / 'react' / 'manifest.json'
    assets = {'js': None, 'css': []}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        entry = manifest.get('index.html', {})
        if entry.get('file'):
            assets['js'] = static('react/' + entry['file'])
        assets['css'] = [static('react/' + path) for path in entry.get('css', [])]
    user = get_user(request)
    account = get_user_account(request)
    payload = {
        'page': page,
        'data': data or {},
        'user': user,
        'navProjects': [project_card_payload(project) for project in Project.objects.filter(owner=account)],
        'csrf': '',
        'links': {
            'dashboard': '/', 'login': '/login/', 'demoLogin': '/login/demo/',
            'faceAuth': '/login/face/', 'logout': '/logout/',
            'projects': '/projects/list/', 'createProject': '/projects/create/',
            'allProjects': '/projects/', 'tasks': '/manage/tasks/',
            'agents': '/manage/agents/', 'results': '/manage/results/',
            'comingSoon': '/coming-soon/', 'comingSoonManage': '/coming-soon/manage/',
            'faq': '/faq/', 'guide': '/user-guide/', 'notifications': '/notifications/',
        },
        'notifications': get_user_notifications(account),
        'csrfToken': request.META.get('CSRF_COOKIE', ''),
    }
    template = 'react/app.html' if shell else 'react/auth.html'
    return render(request, template, {
        'assets': assets,
        'page_styles': PAGE_STYLES.get(page, []),
        'page_scripts': PAGE_SCRIPTS.get(page, []),
        'page': page,
        'active_menu': active_menu,
        'sb_react_data': payload,
        'shell': shell,
    }, status=status)
