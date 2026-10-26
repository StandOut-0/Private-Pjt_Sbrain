import json

from apps.artifacts.models import Artifact
from apps.projects.models import Project


def persist_prd_artifact(execution):
    """Save the immutable PRD output as a new project-scoped Artifact version."""
    payload = json.loads(execution.output)
    project = Project.objects.select_for_update().get(pk=execution.task.project_id)
    logical_key = 'planning-prd'
    existing = Artifact.objects.filter(agent_execution=execution).first()
    if existing:
        return existing
    version = str(Artifact.objects.filter(project=project, logical_key=logical_key).count() + 1)
    return Artifact.objects.create(
        project=project,
        task=execution.task,
        agent_execution=execution,
        artifact_type='prd',
        title=payload['title'],
        description=payload['summary'],
        logical_key=logical_key,
        version=version,
        content=json.dumps(payload, ensure_ascii=False, indent=2),
        mime_type='application/json; charset=utf-8',
    )
