import markdown
from django.http import Http404
from django.shortcuts import redirect

from apps.accounts.session import admin_required, login_required
from apps.comingsoon import storage
from apps.react_pages import render_react


def _render_markdown(body):
    return markdown.markdown(body, extensions=['fenced_code', 'tables'])


@login_required
def index(request):
    context = {
        'documents': storage.list_documents(),
        'active_menu': 'comingsoon',
    }
    return render_react(request, 'comingsoon-list', context, active_menu='comingsoon')


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
    return render_react(request, 'comingsoon-detail', context, active_menu='comingsoon')


@login_required
def blocked(request):
    """관리자 전용 메뉴에 접근한 일반 / 체험 사용자 안내 화면."""
    return render_react(request, 'blocked', active_menu='comingsoon')


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
    return render_react(request, 'comingsoon-manage', context, active_menu='comingsoon_manage')


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
        try:
            new_slug = storage.save_document(slug, meta, request.POST.get('body', ''))
        except ValueError as exc:
            document.update(meta)
            document['body'] = request.POST.get('body', '')
            context = {
                'document': document,
                'statuses': storage.STATUS_CHOICES,
                'categories': storage.CATEGORY_CHOICES,
                'active_menu': 'comingsoon_manage',
                'error': str(exc),
            }
            return render_react(request, 'comingsoon-editor', context, active_menu='comingsoon_manage', status=400)
        return redirect('comingsoon:editor', slug=new_slug)

    context = {
        'document': document,
        'statuses': storage.STATUS_CHOICES,
        'categories': storage.CATEGORY_CHOICES,
        'active_menu': 'comingsoon_manage',
    }
    return render_react(request, 'comingsoon-editor', context, active_menu='comingsoon_manage')


@admin_required
def delete(request, slug):
    if request.method == 'POST':
        storage.delete_document(slug)
    return redirect('comingsoon:manage')
