from django.shortcuts import redirect, render

from apps.accounts.session import (
    ROLE_ADMIN,
    ROLE_DEMO,
    ROLE_USER,
    login_required,
    sign_in,
    sign_out,
)

DEMO_CODE = 'SECONDBRAIN'


def login(request):
    if request.method == 'POST':
        provider = request.POST.get('provider')
        if provider == 'google-admin':
            sign_in(request, '관리자', ROLE_ADMIN, 'admin@secondbrain.dev')
            return redirect('accounts:face_auth')
        sign_in(request, 'Sanghee', ROLE_USER, 'user@secondbrain.dev')
        return redirect('dashboard:index')
    return render(request, 'accounts/login.html')


def demo_login(request):
    error = None
    if request.method == 'POST':
        if request.POST.get('code', '').strip().upper() == DEMO_CODE:
            sign_in(request, 'Demo User', ROLE_DEMO)
            return redirect('dashboard:index')
        error = '인증 코드가 올바르지 않습니다. 다시 입력해주세요.'
    return render(request, 'accounts/demo_login.html', {'error': error, 'demo_code': DEMO_CODE})


def face_auth(request):
    error = None
    if request.method == 'POST':
        if request.POST.get('result') == 'success':
            return redirect('dashboard:index')
        error = '얼굴 인증에 실패했습니다. 다시 시도해주세요.'
    return render(request, 'accounts/face_auth.html', {'error': error})


@login_required
def logout(request):
    sign_out(request)
    return redirect('accounts:login')
