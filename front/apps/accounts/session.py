"""세션 기반 임시 인증 유틸.

Google OAuth / Face Recognition 연동 전까지 세션에 사용자 정보를 저장한다.
"""

import secrets
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
    from apps.accounts.models import UserAccount

    request.session.cycle_key()
    normalized_email = email.strip().casefold() or None
    if role == ROLE_DEMO:
        guest_identity = request.session.get('sb_guest_identity')
        if not guest_identity:
            guest_identity = secrets.token_urlsafe(32)
            request.session['sb_guest_identity'] = guest_identity
        identity_key = f'demo-guest:{guest_identity}'
        account_role = UserAccount.ROLE_USER
    else:
        if not normalized_email:
            raise ValueError('A persistent sign-in requires a stable email identity.')
        request.session.pop('sb_guest_identity', None)
        identity_key = f'local:{normalized_email}'
        account_role = UserAccount.ROLE_ADMIN if role == ROLE_ADMIN else UserAccount.ROLE_USER

    account, _ = UserAccount.objects.update_or_create(
        identity_key=identity_key,
        defaults={
            'name': name,
            'email': normalized_email,
            'role': account_role,
        },
    )
    request.session[SESSION_KEY] = {
        'user_id': account.pk,
        'name': name,
        'role': role,
        'email': normalized_email or '',
        'role_label': ROLE_LABELS[role],
        'is_admin': role == ROLE_ADMIN,
    }


def sign_out(request):
    request.session.flush()


def get_user(request):
    return request.session.get(SESSION_KEY)


def get_user_account(request):
    user = get_user(request)
    if not user or not user.get('user_id'):
        return None

    from apps.accounts.models import UserAccount

    return UserAccount.objects.filter(pk=user['user_id']).first()


def login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not get_user_account(request):
            return redirect('accounts:login')
        return view(request, *args, **kwargs)

    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        account = get_user_account(request)
        if not account:
            return redirect('accounts:login')
        if account.role != 'admin':
            return redirect('comingsoon:blocked')
        return view(request, *args, **kwargs)

    return wrapper
