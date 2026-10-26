from apps.execution.models import ExecutionEvent


def record_event(*, project, event_type, message, run=None, task=None, execution=None,
                 from_status='', to_status='', metadata=None):
    return ExecutionEvent.objects.create(
        project=project, run=run, task=task, execution=execution,
        event_type=event_type, from_status=from_status, to_status=to_status,
        message=message[:300], metadata=metadata or {},
    )


def event_payload(event):
    status = 'done' if event.to_status == 'succeeded' else 'failed' if event.to_status == 'failed' else 'running' if event.to_status in ('running', 'queued') else event.to_status
    return {'id': event.pk, 'type': event.event_type, 'run_id': event.run_id, 'task_id': event.task_id,
            'execution_id': event.execution_id, 'from_status': event.from_status, 'to_status': event.to_status,
            'message': event.message, 'title': event.message, 'agent': 'Planning Agent' if event.execution_id else 'Supervisor',
            'status': status, 'time': event.created_at.isoformat().replace('+00:00', 'Z'), 'metadata': event.metadata}
