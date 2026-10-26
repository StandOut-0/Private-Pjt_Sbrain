import json

from apps.artifacts.models import Artifact


def persist_prd_artifact(execution):
    """Save the immutable PRD output as a new project-scoped Artifact version."""
    payload = json.loads(execution.output)
    project = execution.task.project
    logical_key = 'planning-prd'
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
