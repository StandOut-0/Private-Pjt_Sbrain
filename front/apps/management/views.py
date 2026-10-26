import base64
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.text import get_valid_filename

from apps import mockdata
from apps.accounts.models import AdminFacePhoto
from apps.accounts.session import admin_required, get_user_account
from apps.artifacts.models import Artifact
from apps.execution.models import AgentExecution
from apps.management.models import KnowledgeDocument
from apps.execution.models import Task
from apps.projects.models import Project
from apps.reflection.models import QualityCriterion
from apps.react_pages import render_react
from datetime import timedelta

MAX_FACE_PHOTO_BYTES = 5 * 1024 * 1024
FACE_IMAGE_SIGNATURES = (
    ('image/jpeg', lambda data: data.startswith(b'\xff\xd8\xff')),
    ('image/png', lambda data: data.startswith(b'\x89PNG\r\n\x1a\n')),
    ('image/webp', lambda data: len(data) >= 12 and data[:4] == b'RIFF' and data[8:12] == b'WEBP'),
)


def _face_photo_payload(account):
    photo = AdminFacePhoto.objects.filter(account=account).first()
    if not photo:
        return None
    encoded = base64.b64encode(bytes(photo.image_data)).decode('ascii')
    return {
        'data_url': f'data:{photo.content_type};base64,{encoded}',
        'updated_at': timezone.localtime(photo.updated_at).strftime('%Y-%m-%d %H:%M'),
    }


@admin_required
def task_list(request):
    keyword = request.GET.get('q', '').strip()
    project = request.GET.get('project', '')
    status = request.GET.get('status', '')

    queryset = Task.objects.select_related('project').prefetch_related('executions__agent').all()
    if keyword:
        queryset = queryset.filter(title__icontains=keyword)
    if project:
        queryset = queryset.filter(project__project_name=project)
    status_values = {'running': [Task.STATUS_RUNNING], 'done': [Task.STATUS_SUCCEEDED],
                     'failed': [Task.STATUS_FAILED, Task.STATUS_CANCELLED], 'waiting': [Task.STATUS_QUEUED, Task.STATUS_WAITING_FOR_USER]}
    if status in status_values:
        queryset = queryset.filter(status__in=status_values[status])
    all_tasks = list(Task.objects.all())
    task_rows = []
    for task in queryset[:200]:
        execution = task.executions.select_related('agent').first()
        state = {'queued': 'waiting', 'waiting_for_user': 'waiting', 'running': 'running',
                 'succeeded': 'done', 'failed': 'failed', 'cancelled': 'failed'}.get(task.status, 'waiting')
        elapsed = None
        if task.started_at and task.finished_at:
            elapsed = max(0, int((task.finished_at - task.started_at).total_seconds()))
        task_rows.append({
            'id': task.pk, 'started_at': (task.started_at or task.created_at).strftime('%Y-%m-%d %H:%M'),
            'agent': execution.agent.name if execution else 'Supervisor', 'name': task.title,
            'project': task.project.project_name, 'status': state,
            'status_label': {'waiting': '대기', 'running': '진행 중', 'done': '완료', 'failed': '실패'}[state],
            'duration': f'{elapsed} sec' if elapsed is not None else '미계측',
            'input_tokens': execution.input_tokens if execution else None,
            'output_tokens': execution.output_tokens if execution else None,
            'total_tokens': execution.input_tokens + execution.output_tokens if execution and execution.input_tokens is not None and execution.output_tokens is not None else None,
            'provider': execution.provider_name if execution else '미실행',
            'model': execution.model_name if execution else '미계측',
            'cost_usd': str(execution.estimated_cost_usd) if execution and execution.estimated_cost_usd is not None else None,
            'error_code': execution.error_code if execution else '',
        })

    completed = [task for task in all_tasks if task.status in (Task.STATUS_SUCCEEDED, Task.STATUS_FAILED, Task.STATUS_CANCELLED)]
    successes = sum(task.status == Task.STATUS_SUCCEEDED for task in completed)
    failures = sum(task.status in (Task.STATUS_FAILED, Task.STATUS_CANCELLED) for task in completed)
    durations = [(task.finished_at-task.started_at).total_seconds() for task in completed if task.started_at and task.finished_at]
    metrics = {
        'success_rate': f'{successes / len(completed) * 100:.1f}%' if completed else '—',
        'avg_duration': f'{sum(durations) / len(durations):.1f} sec' if durations else '미계측',
        'error_rate': f'{failures / len(completed) * 100:.1f}%' if completed else '—',
    }
    today = timezone.localdate()
    daily_labels = [(today-timedelta(days=6-i)).strftime('%m/%d') for i in range(7)]
    daily_values = [sum(task.created_at.date() == (today-timedelta(days=6-i)) for task in all_tasks) for i in range(7)]
    weekly_labels = [f'{3-i}주 전' if i < 3 else '이번 주' for i in range(4)]
    weekly_values = [sum((today-task.created_at.date()).days // 7 == (3-i) for task in all_tasks if task.created_at.date() <= today) for i in range(4)]

    context = {
        'tasks': task_rows,
        'projects': [{'id': project.pk, 'title': project.project_name} for project in Project.objects.order_by('project_name')],
        'metrics': metrics,
        'trend': {'daily': daily_values, 'daily_labels': daily_labels, 'weekly': weekly_values, 'weekly_labels': weekly_labels},
        'executions': task_rows,
        'filters': {'q': keyword, 'project': project, 'status': status},
        'active_menu': 'tasks',
    }
    return render_react(request, 'tasks', context, active_menu='tasks')


@admin_required
def agent_list(request):
    catalog = mockdata.get_agents()
    workers = [_agent_runtime_payload(agent) for agent in mockdata.get_worker_agents()]
    supervisor = _agent_runtime_payload(mockdata.get_agent('supervisor'))
    agents = [supervisor, *workers]
    context = {
        'supervisor': supervisor,
        'workers': workers,
        'running_count': sum(agent['status'] == 'running' for agent in agents),
        'total_count': len(catalog),
        'active_menu': 'agents',
    }
    return render_react(request, 'agents', context, active_menu='agents')


def _agent_runtime_payload(catalog_agent):
    """Keep role descriptions as catalog data, but derive all operational claims from executions."""
    agent = dict(catalog_agent)
    execution = AgentExecution.objects.filter(agent__key=agent['key']).select_related(
        'task__project'
    ).first()
    if execution is None:
        agent.update({
            'status': 'waiting', 'status_label': '미실행',
            'project': '실행 이력 없음', 'task': '아직 실행된 작업이 없습니다.',
            'steps': [],
            'metrics': [{'label': '실행 횟수', 'value': '0'}, {'label': '성공률', 'value': '—'}, {'label': '평균 실행시간', 'value': '—'}],
        })
        return agent

    state = {
        AgentExecution.STATUS_QUEUED: ('waiting', '대기'),
        AgentExecution.STATUS_RUNNING: ('running', '실행 중'),
        AgentExecution.STATUS_CANCEL_REQUESTED: ('running', '중단 요청'),
        AgentExecution.STATUS_SUCCEEDED: ('done', '완료'),
        AgentExecution.STATUS_FAILED: ('failed', '실패'),
        AgentExecution.STATUS_CANCELLED: ('failed', '취소'),
    }.get(execution.status, ('waiting', execution.get_status_display()))
    all_executions = AgentExecution.objects.filter(agent__key=agent['key'])
    succeeded = all_executions.filter(status=AgentExecution.STATUS_SUCCEEDED).count()
    total = all_executions.count()
    durations = [
        (item.finished_at - item.started_at).total_seconds()
        for item in all_executions.filter(started_at__isnull=False, finished_at__isnull=False)
    ]
    agent.update({
        'status': state[0], 'status_label': state[1],
        'project': execution.task.project.project_name,
        'task': execution.task.title,
        'steps': [{'name': 'Agent 실행', 'state': 'done' if execution.status in (AgentExecution.STATUS_SUCCEEDED, AgentExecution.STATUS_FAILED, AgentExecution.STATUS_CANCELLED) else ('running' if execution.status == AgentExecution.STATUS_RUNNING else 'todo')}],
        'metrics': [
            {'label': '실행 횟수', 'value': str(total)},
            {'label': '성공률', 'value': f'{succeeded / total * 100:.1f}%' if total else '—'},
            {'label': '평균 실행시간', 'value': f'{sum(durations) / len(durations):.1f} sec' if durations else '미계측'},
        ],
    })
    return agent


@admin_required
def agent_detail(request, key):
    catalog_agent = mockdata.get_agent(key)
    if not catalog_agent:
        raise Http404('agent not found')
    agent = _agent_runtime_payload(catalog_agent)
    context = {
        'agent': agent,
        'children': [_agent_runtime_payload(mockdata.get_agent(child)) for child in agent['children']],
        'criteria': [
            {'key': item.key, 'label': item.label, 'description': item.description,
             'weight': item.weight, 'is_active': item.is_active, 'sort_order': item.sort_order}
            for item in QualityCriterion.objects.all()
        ] if key == 'reflection' else [],
        'active_menu': 'agents',
        'active_agent': key,
    }
    return render_react(request, 'agent-detail', context, active_menu='agents')


@admin_required
def results(request):
    project_id = request.GET.get('project', '')
    keyword = request.GET.get('q', '').strip()
    projects = list(Project.objects.order_by('project_name'))
    selected_project = next((project for project in projects if str(project.pk) == project_id), None)
    selected = {'id': selected_project.pk, 'title': selected_project.project_name} if selected_project else None
    artifacts = Artifact.objects.select_related('project', 'agent_execution__agent').order_by('-created_at', '-id')
    if selected_project:
        artifacts = artifacts.filter(project=selected_project)
    if keyword:
        artifacts = artifacts.filter(title__icontains=keyword)
    grouped_artifacts = {}
    for artifact in artifacts:
        grouped_artifacts.setdefault(artifact.project.project_name, []).append({
            'id': artifact.pk,
            'name': f'{artifact.title}.json',
            'kind': 'text',
            'agent': artifact.agent_execution.agent.name,
            'size': f'{len(artifact.content.encode("utf-8")):,} bytes',
            'updated_at': timezone.localtime(artifact.created_at).strftime('%Y-%m-%d %H:%M'),
            'detail_url': f'/api/v1/projects/{artifact.project_id}/artifacts/{artifact.pk}/',
            'download_url': f'/api/v1/projects/{artifact.project_id}/artifacts/{artifact.pk}/download/',
        })
    tree = [{'name': name, 'files': files} for name, files in grouped_artifacts.items()]
    rag_query = request.GET.get('rag_q', '').strip()
    rag_project = request.GET.get('rag_project', '')
    rag_status = request.GET.get('rag_status', '')
    knowledge_documents = KnowledgeDocument.objects.select_related('project')
    if rag_query:
        knowledge_documents = knowledge_documents.filter(title__icontains=rag_query)
    if rag_project:
        knowledge_documents = knowledge_documents.filter(project__project_name=rag_project)
    if rag_status and rag_status != '키워드 검색 가능 · 벡터 미색인':
        knowledge_documents = knowledge_documents.none()
    vector_documents = [{
        'project': document.project.project_name if document.project else '전체 공통',
        'document': document.title,
        'chunks': '키워드',
        'status': '키워드 검색 가능 · 벡터 미색인',
    } for document in knowledge_documents]
    upload_error = ''
    if request.method == 'POST' and request.POST.get('action') == 'knowledge-upload':
        upload = request.FILES.get('file')
        scope = request.POST.get('scope', KnowledgeDocument.SCOPE_GLOBAL)
        project_id_value = request.POST.get('project', '').strip()
        project = Project.objects.filter(pk=project_id_value).first() if project_id_value.isdigit() else None
        if not upload:
            upload_error = '업로드할 TXT 또는 Markdown 파일을 선택해주세요.'
        elif upload.size > 1_048_576:
            upload_error = '문서 파일은 1MB 이하로 업로드해주세요.'
        elif Path(upload.name).suffix.casefold() not in {'.txt', '.md'}:
            upload_error = '현재는 TXT와 Markdown 파일만 저장할 수 있습니다.'
        elif scope not in {KnowledgeDocument.SCOPE_GLOBAL, KnowledgeDocument.SCOPE_PROJECT}:
            upload_error = '문서 적용 범위를 선택해주세요.'
        elif scope == KnowledgeDocument.SCOPE_PROJECT and project is None:
            upload_error = '프로젝트별 문서에는 프로젝트를 선택해주세요.'
        else:
            try:
                content = upload.read(1_048_577).decode('utf-8-sig')
            except UnicodeDecodeError:
                upload_error = 'UTF-8 인코딩 문서만 업로드할 수 있습니다.'
            else:
                if len(content.encode('utf-8')) > 1_048_576:
                    upload_error = '문서 파일은 1MB 이하로 업로드해주세요.'
                elif not content.strip():
                    upload_error = '내용이 비어 있는 문서는 등록할 수 없습니다.'
                else:
                    KnowledgeDocument.objects.create(
                        title=Path(upload.name).stem[:200],
                        original_name=get_valid_filename(upload.name)[:255],
                        scope=scope,
                        project=project if scope == KnowledgeDocument.SCOPE_PROJECT else None,
                        content=content,
                        uploaded_by=get_user_account(request),
                    )
                    return redirect('/manage/results/?tab=knowledge&uploaded=1')
    knowledge_documents = KnowledgeDocument.objects.all()
    document_count = knowledge_documents.count()
    context = {
        'projects': [{'id': project.pk, 'title': project.project_name} for project in projects],
        'selected': selected,
        'results_tab': 'knowledge' if request.GET.get('tab') == 'knowledge' else 'files',
        'rag_filters': {'q': rag_query, 'project': rag_project, 'status': rag_status},
        'rag_statuses': ['키워드 검색 가능 · 벡터 미색인'],
        'keyword': keyword,
        'tree': tree,
        'knowledge_stats': [
            {'label': '등록 문서', 'value': document_count},
            {'label': '전체 공통', 'value': knowledge_documents.filter(scope=KnowledgeDocument.SCOPE_GLOBAL).count()},
            {'label': '프로젝트별', 'value': knowledge_documents.filter(scope=KnowledgeDocument.SCOPE_PROJECT).count()},
            {'label': '벡터 색인', 'value': '미연결'},
        ],
        'vector_documents': vector_documents,
        'search_metrics': [],
        'upload_error': upload_error,
        'uploaded': request.GET.get('uploaded') == '1',
        'active_menu': 'results',
        'statuses': ['키워드 검색 가능 · 벡터 미색인'],
        'zip_url': f'/manage/results/download.zip{"?project=" + str(selected_project.pk) if selected_project else ""}',
    }
    return render_react(request, 'results', context, status=400 if upload_error else 200, active_menu='results')


@admin_required
def download_results_zip(request):
    project_id = request.GET.get('project', '')
    artifacts = Artifact.objects.select_related('project').order_by('project__project_name', 'created_at', 'id')
    if project_id:
        artifacts = artifacts.filter(project_id=project_id)
    buffer = BytesIO()
    with ZipFile(buffer, 'w', ZIP_DEFLATED) as archive:
        for artifact in artifacts:
            folder = get_valid_filename(artifact.project.project_name) or f'project-{artifact.project_id}'
            title = get_valid_filename(artifact.title) or f'artifact-{artifact.pk}'
            archive.writestr(f'{folder}/{title}-v{artifact.version}.json', artifact.content)
    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="sbrain-results.zip"'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@admin_required
def face_photo(request):
    account = get_user_account(request)
    error = ''
    saved = request.GET.get('saved') == '1'
    if request.method == 'POST':
        if request.POST.get('action') == 'delete':
            AdminFacePhoto.objects.filter(account=account).delete()
            return redirect(f'{request.path}?removed=1')
        upload = request.FILES.get('photo')
        if not upload:
            error = '등록할 사진을 선택해주세요.'
        elif upload.size > MAX_FACE_PHOTO_BYTES:
            error = '사진은 5MB 이하로 등록해주세요.'
        else:
            image_data = upload.read(MAX_FACE_PHOTO_BYTES + 1)
            image_type = next((mime for mime, check in FACE_IMAGE_SIGNATURES if check(image_data)), None)
            if len(image_data) > MAX_FACE_PHOTO_BYTES:
                error = '사진은 5MB 이하로 등록해주세요.'
            elif image_type is None:
                error = 'JPEG, PNG, WEBP 이미지 파일만 등록할 수 있습니다.'
            else:
                AdminFacePhoto.objects.update_or_create(
                    account=account,
                    defaults={'image_data': image_data, 'content_type': image_type},
                )
                return redirect(f'{request.path}?saved=1')

    context = {
        'face_photo': _face_photo_payload(account),
        'error': error,
        'saved': saved,
        'removed': request.GET.get('removed') == '1',
        'active_menu': 'face_photo',
    }
    return render_react(request, 'face-photo', context, status=400 if error else 200, active_menu='face_photo')
