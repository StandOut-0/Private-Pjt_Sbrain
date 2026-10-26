from django.shortcuts import redirect

from apps.accounts.session import (
    ROLE_ADMIN,
    ROLE_DEMO,
    ROLE_USER,
    login_required,
    sign_in,
    sign_out,
)
from apps.accounts.models import UserAccount
from apps.react_pages import render_react

DEMO_CODE = 'SECONDBRAIN'


def login(request):
    if request.method == 'POST':
        provider = request.POST.get('provider')
        if provider == 'google-admin':
            sign_in(request, '관리자', ROLE_ADMIN, 'admin@secondbrain.dev')
            return redirect('accounts:face_auth')
        sign_in(request, 'Sanghee', ROLE_USER, 'user@secondbrain.dev')
        return redirect('dashboard:index')
    return render_react(request, 'login', shell=False)


def demo_login(request):
    error = None
    if request.method == 'POST':
        if request.POST.get('code', '').strip().upper() == DEMO_CODE:
            sign_in(request, 'Demo User', ROLE_DEMO)
            return redirect('dashboard:index')
        error = '인증 코드가 올바르지 않습니다. 다시 입력해주세요.'
    return render_react(request, 'demo-login', {'error': error}, shell=False)


def face_auth(request):
    error = None
    if request.method == 'POST':
        if request.POST.get('result') == 'success':
            account = get_user_account(request)
            if account and account.role == UserAccount.ROLE_ADMIN:
                return redirect('management:tasks')
            return redirect('dashboard:index')
        error = '얼굴 인증에 실패했습니다. 다시 시도해주세요.'
    return render_react(request, 'face-auth', {'error': error}, shell=False)


@login_required
def logout(request):
    sign_out(request)
    return redirect('accounts:login')
