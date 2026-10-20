from django.db import transaction

from apps.projects.models import Conversation, Message, Project


class ProjectInputError(ValueError):
    pass


@transaction.atomic
def create_project(*, owner, title, summary='', initial_message=None):
    if not isinstance(title, str) or not isinstance(summary, str):
        raise ProjectInputError('프로젝트 이름과 설명은 문자열이어야 합니다.')
    if initial_message is not None and not isinstance(initial_message, str):
        raise ProjectInputError('프로젝트 목표는 문자열이어야 합니다.')
    title = title.strip()
    summary = summary.strip()
    has_initial_message = initial_message is not None
    initial_message = initial_message.strip() if has_initial_message else ''
    if not 2 <= len(title) <= 80:
        raise ProjectInputError('프로젝트 이름은 2자 이상 80자 이하여야 합니다.')
    if len(summary) > 500:
        raise ProjectInputError('한 줄 설명은 500자 이하여야 합니다.')
    if has_initial_message and not 1 <= len(initial_message) <= 10000:
        raise ProjectInputError('프로젝트 목표는 1자 이상 10,000자 이하여야 합니다.')

    project = Project.objects.create(
        owner=owner,
        project_name=title,
        description=summary,
    )
    if has_initial_message:
        conversation = Conversation.objects.create(
            project=project,
            owner=owner,
            title=title,
        )
        Message.objects.create(
            conversation=conversation,
            role=Message.ROLE_USER,
            content=initial_message,
        )
    return project


@transaction.atomic
def update_project(project, *, title=None, summary=None, status=None):
    update_fields = []
    if title is not None:
        if not isinstance(title, str):
            raise ProjectInputError('프로젝트 이름은 문자열이어야 합니다.')
        title = title.strip()
        if not 2 <= len(title) <= 80:
            raise ProjectInputError('프로젝트 이름은 2자 이상 80자 이하여야 합니다.')
        project.project_name = title
        update_fields.append('project_name')
    if summary is not None:
        if not isinstance(summary, str):
            raise ProjectInputError('한 줄 설명은 문자열이어야 합니다.')
        summary = summary.strip()
        if len(summary) > 500:
            raise ProjectInputError('한 줄 설명은 500자 이하여야 합니다.')
        project.description = summary
        update_fields.append('description')
    if status is not None:
        if not isinstance(status, str):
            raise ProjectInputError('프로젝트 상태는 문자열이어야 합니다.')
        if status not in {value for value, _label in Project.STATUS_CHOICES}:
            raise ProjectInputError('지원하지 않는 프로젝트 상태입니다.')
        project.status = status
        update_fields.append('status')
    if update_fields:
        update_fields.append('updated_at')
        project.save(update_fields=update_fields)
    return project
