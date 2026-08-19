import markdown
from django.http import Http404
from django.shortcuts import redirect, render

from apps.accounts.session import admin_required, login_required
from apps.comingsoon import storage


def _render_markdown(body):
    return markdown.markdown(body, extensions=['fenced_code', 'tables'])


@login_required
def index(request):
    context = {
        'documents': storage.list_documents(),
        'active_menu': 'comingsoon',
    }
    return render(request, 'comingsoon/index.html', context)


@login_required
def detail(request, slug):
    document = storage.read_document(slug)
    if not document:
        raise Http404('coming soon document not found')
    context = {
        'document': document,
        'body_html': _render_markdown(document['body']),
        'active_menu': 'comingsoon',
    }
    return render(request, 'comingsoon/detail.html', context)


@login_required
def blocked(request):
    """관리자 전용 메뉴에 접근한 일반 / 체험 사용자 안내 화면."""
    return render(request, 'comingsoon/blocked.html', {'active_menu': 'comingsoon'})


@admin_required
def manage(request):
    keyword = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    category = request.GET.get('category', '')
    context = {
        'documents': storage.list_documents(keyword, status, category),
        'filters': {'q': keyword, 'status': status, 'category': category},
        'statuses': storage.STATUS_CHOICES,
        'categories': storage.CATEGORY_CHOICES,
        'active_menu': 'comingsoon_manage',
    }
    return render(request, 'comingsoon/manage.html', context)


@admin_required
def editor(request, slug=None):
    document = storage.read_document(slug) if slug else dict(storage.META_FORM, slug='', body='')
    if slug and not document:
        raise Http404('coming soon document not found')

    if request.method == 'POST':
        meta = {
            'title': request.POST.get('title', '').strip(),
            'summary': request.POST.get('summary', '').strip(),
            'status': request.POST.get('status', storage.STATUS_CHOICES[0]),
            'category': request.POST.get('category', storage.CATEGORY_CHOICES[0]),
            'technologies': request.POST.get('technologies', ''),
            'related_agents': request.POST.get('related_agents', ''),
            'created_at': document.get('created_at', ''),
        }
        new_slug = storage.save_document(slug, meta, request.POST.get('body', ''))
        return redirect('comingsoon:editor', slug=new_slug)

    context = {
        'document': document,
        'statuses': storage.STATUS_CHOICES,
        'categories': storage.CATEGORY_CHOICES,
        'active_menu': 'comingsoon_manage',
    }
    return render(request, 'comingsoon/editor.html', context)


@admin_required
def delete(request, slug):
    if request.method == 'POST':
        storage.delete_document(slug)
    return redirect('comingsoon:manage')
