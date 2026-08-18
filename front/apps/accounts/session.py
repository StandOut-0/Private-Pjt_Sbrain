"""세션 기반 임시 인증 유틸.

Google OAuth / Face Recognition 연동 전까지 세션에 사용자 정보를 저장한다.
"""

from functools import wraps

from django.shortcuts import redirect

SESSION_KEY = 'sb_user'

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_DEMO = 'demo'

ROLE_LABELS = {
    ROLE_USER: '사용자',
    ROLE_ADMIN: '관리자',
    ROLE_DEMO: '체험 사용자',
}


def sign_in(request, name, role, email=''):
    request.session[SESSION_KEY] = {
        'name': name,
        'role': role,
        'email': email,
        'role_label': ROLE_LABELS[role],
        'is_admin': role == ROLE_ADMIN,
    }


def sign_out(request):
    request.session.pop(SESSION_KEY, None)


def get_user(request):
    return request.session.get(SESSION_KEY)


def login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not get_user(request):
            return redirect('accounts:login')
        return view(request, *args, **kwargs)

    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        user = get_user(request)
        if not user:
            return redirect('accounts:login')
        if not user['is_admin']:
            return redirect('comingsoon:blocked')
        return view(request, *args, **kwargs)

    return wrapper
