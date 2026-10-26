import json
import uuid

from django.core.management import call_command
from django.db import IntegrityError
from django.test import Client, TestCase, override_settings

from apps.accounts.models import UserAccount
from apps.execution.models import AgentExecution, ProjectRun, Task
from apps.execution.planning import FakePlanningProvider, PlanningError, process_run
from apps.artifacts.models import Artifact
from apps.projects.models import Conversation, Message, Project
from apps.projects.ownership import project_card_payload
from apps.execution.models import ExecutionEvent


class FailingProvider:
    def generate(self, request):
        raise PlanningError('PROVIDER_TIMEOUT', '기획 Provider 응답 시간이 초과됐습니다.', retryable=True)


class InvalidProvider:
    def generate(self, request):
        return {'title': 'incomplete'}


class CancelDuringProvider:
    def __init__(self, run_id, client=None, project_id=None):
        self.run_id = run_id
        self.client = client
        self.project_id = project_id
        self.cancel_statuses = []

    def generate(self, request):
        if self.client:
            response = self.client.post(f'/api/v1/projects/{self.project_id}/runs/{self.run_id}/cancel/')
            self.cancel_statuses.append(response.status_code)
            repeated = self.client.post(f'/api/v1/projects/{self.project_id}/runs/{self.run_id}/cancel/')
            self.cancel_statuses.append(repeated.status_code)
        else:
            ProjectRun.objects.filter(pk=self.run_id).update(status=ProjectRun.STATUS_CANCEL_REQUESTED)
        return FakePlanningProvider().generate(request)


class PlanningExecutionTests(TestCase):
    def setUp(self):
        self.owner = UserAccount.objects.create(identity_key='local:planning@example.test', name='Planning User')
        self.project = Project.objects.create(owner=self.owner, project_name='Planning sample')
        self.conversation = Conversation.objects.create(project=self.project, owner=self.owner, title='Planning')
        self.message = Message.objects.create(
            conversation=self.conversation,
            role=Message.ROLE_USER,
            content='Create a small shop PRD\nInclude product search and checkout.',
        )
        self.run = ProjectRun.objects.create(
            project=self.project,
            requested_by=self.owner,
            conversation=self.conversation,
            source_message=self.message,
            idempotency_key=str(uuid.uuid4()),
        )

    def test_fake_provider_generates_repeatable_contract_output(self):
        request = {
            'objective': 'Create a small shop PRD',
            'known_requirements': ['Include product search and checkout.'],
            'request_type': 'general',
        }

        first = FakePlanningProvider().generate(request)
        second = FakePlanningProvider().generate(request)

        self.assertEqual(first, second)
        self.assertEqual(first['functional_requirements'], ['Include product search and checkout.'])

    def test_worker_completes_run_and_stores_structured_prd(self):
        run = process_run(self.run.pk, FakePlanningProvider())

        run.refresh_from_db()
        task = Task.objects.get(run=run)
        execution = AgentExecution.objects.get(task=task)
        result = json.loads(execution.output)
        self.assertEqual(run.status, ProjectRun.STATUS_SUCCEEDED)
        self.assertEqual(task.status, Task.STATUS_SUCCEEDED)
        self.assertEqual(execution.status, AgentExecution.STATUS_SUCCEEDED)
        self.assertEqual(result['objective'], 'Create a small shop PRD')
        self.assertEqual(result['functional_requirements'], ['Include product search and checkout.'])
        self.assertIsNotNone(run.finished_at)
        artifact = Artifact.objects.get(task=task)
        self.assertEqual(artifact.project, self.project)
        self.assertEqual(json.loads(artifact.content), result)

        process_run(run.pk, FakePlanningProvider())
        self.assertEqual(AgentExecution.objects.filter(task=task).count(), 1)
        self.assertEqual(Artifact.objects.filter(task=task).count(), 1)
        events = list(ExecutionEvent.objects.filter(run=run).order_by('created_at', 'id'))
        self.assertEqual([event.event_type for event in events], ['agent.started', 'agent.succeeded', 'run.succeeded'])
        self.assertEqual(len(project_card_payload(self.project)['activities']), 3)

    def test_artifact_endpoints_enforce_project_ownership_and_download_json(self):
        run = process_run(self.run.pk, FakePlanningProvider())
        artifact = Artifact.objects.get(task=run.planning_task)
        client = Client()
        session = client.session
        session['sb_user'] = {'user_id': self.owner.pk, 'role': 'user'}
        session.save()

        listing = client.get(f'/api/v1/projects/{self.project.pk}/artifacts/')
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.json()['items'][0]['id'], artifact.pk)
        detail = client.get(f'/api/v1/projects/{self.project.pk}/artifacts/{artifact.pk}/')
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()['content'], artifact.content)
        download = client.get(f'/api/v1/projects/{self.project.pk}/artifacts/{artifact.pk}/download/')
        self.assertEqual(download.status_code, 200)
        self.assertIn('attachment;', download['Content-Disposition'])
        self.assertEqual(download['X-Content-Type-Options'], 'nosniff')
        self.assertTrue(download['Content-Type'].startswith('application/json'))
        self.assertEqual(json.loads(download.content), json.loads(artifact.content))

        other = UserAccount.objects.create(identity_key='local:other@example.test', name='Other')
        other_project = Project.objects.create(owner=other, project_name='Other project')
        denied = client.get(f'/api/v1/projects/{other_project.pk}/artifacts/')
        self.assertEqual(denied.status_code, 404)
        cross_project = client.get(f'/api/v1/projects/{other_project.pk}/artifacts/{artifact.pk}/download/')
        self.assertEqual(cross_project.status_code, 404)

    def test_run_api_rejects_oversized_json_body(self):
        response = self._logged_client().post(
            f'/api/v1/projects/{self.project.pk}/runs/',
            data='x' * 65537,
            content_type='application/json',
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()['error']['code'], 'REQUEST_TOO_LARGE')

    def test_provider_failure_is_structured_and_does_not_leak_internal_details(self):
        run = process_run(self.run.pk, FailingProvider())
        execution = AgentExecution.objects.get(task__run=run)
        self.assertEqual(run.status, ProjectRun.STATUS_FAILED)
        self.assertEqual(run.planning_task.status, Task.STATUS_FAILED)
        self.assertEqual(execution.error_code, 'PROVIDER_TIMEOUT')
        self.assertEqual(execution.error_message, '기획 Provider 응답 시간이 초과됐습니다.')
        self.assertTrue(execution.is_retryable)
        self.assertTrue(execution.error_message)
        self.assertEqual(execution.output, '')

    def test_invalid_provider_output_becomes_safe_failure(self):
        run = process_run(self.run.pk, InvalidProvider())
        execution = AgentExecution.objects.get(task__run=run)
        self.assertEqual(run.status, ProjectRun.STATUS_FAILED)
        self.assertEqual(execution.error_code, 'INVALID_PROVIDER_OUTPUT')
        self.assertNotIn('stack', execution.error_message.casefold())

    def test_artifact_persistence_failure_finishes_run_in_failed_state(self):
        from unittest.mock import patch
        with patch('apps.execution.artifacts.persist_prd_artifact', side_effect=IntegrityError('duplicate artifact')):
            run = process_run(self.run.pk, FakePlanningProvider())
        run.refresh_from_db()
        execution = AgentExecution.objects.get(task__run=run)
        self.assertEqual(run.status, ProjectRun.STATUS_FAILED)
        self.assertEqual(run.planning_task.status, Task.STATUS_FAILED)
        self.assertEqual(execution.status, AgentExecution.STATUS_FAILED)
        self.assertEqual(execution.error_code, 'ARTIFACT_PERSIST_FAILED')
        self.assertEqual(execution.output, '')
        self.assertIsNotNone(run.finished_at)

    @override_settings(DEBUG=False)
    def test_external_provider_is_not_allowed_outside_development(self):
        from unittest.mock import patch
        with patch.dict('os.environ', {'PLANNING_PROVIDER': 'external'}):
            run = process_run(self.run.pk)
        execution = AgentExecution.objects.get(task__run=run)
        self.assertEqual(run.status, ProjectRun.STATUS_FAILED)
        self.assertEqual(execution.error_code, 'PROVIDER_NOT_ALLOWED')

    def test_worker_once_command_is_safe_when_queue_is_empty(self):
        from io import StringIO
        self.run.delete()
        output = StringIO()
        call_command('process_runs', '--once', stdout=output)
        self.assertIn('No queued runs.', output.getvalue())

    def _logged_client(self):
        client = Client()
        session = client.session
        session['sb_user'] = {'user_id': self.owner.pk, 'role': 'user'}
        session.save()
        return client

    def test_retryable_failure_creates_new_run_and_preserves_failed_attempt(self):
        failed = process_run(self.run.pk, FailingProvider())
        response = self._logged_client().post(
            f'/api/v1/projects/{self.project.pk}/runs/{failed.pk}/retry/',
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )
        self.assertEqual(response.status_code, 202)
        retry = ProjectRun.objects.get(pk=response.json()['id'])
        self.assertEqual(retry.previous_run_id, failed.pk)
        self.assertEqual(retry.retry_count, 1)
        self.assertEqual(retry.instruction_snapshot, failed.instruction_snapshot)

        succeeded = process_run(retry.pk, FakePlanningProvider())
        failed.refresh_from_db()
        self.assertEqual(failed.status, ProjectRun.STATUS_FAILED)
        self.assertEqual(succeeded.status, ProjectRun.STATUS_SUCCEEDED)
        self.assertEqual(Artifact.objects.filter(project=self.project).count(), 1)

    def test_retry_is_limited_to_three_retryable_attempts(self):
        current = process_run(self.run.pk, FailingProvider())
        client = self._logged_client()
        for attempt in range(1, 4):
            response = client.post(
                f'/api/v1/projects/{self.project.pk}/runs/{current.pk}/retry/',
                HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
            )
            self.assertEqual(response.status_code, 202)
            current = process_run(response.json()['id'], FailingProvider())
            self.assertEqual(current.retry_count, attempt)
        blocked = client.post(
            f'/api/v1/projects/{self.project.pk}/runs/{current.pk}/retry/',
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )
        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(blocked.json()['error']['code'], 'RETRY_LIMIT_REACHED')

    def test_cancel_requested_during_provider_discards_result(self):
        provider = CancelDuringProvider(self.run.pk, self._logged_client(), self.project.pk)
        run = process_run(self.run.pk, provider)
        run.refresh_from_db()
        execution = AgentExecution.objects.get(task__run=run)
        self.assertEqual(run.status, ProjectRun.STATUS_CANCELLED)
        self.assertEqual(run.planning_task.status, Task.STATUS_CANCELLED)
        self.assertEqual(execution.status, AgentExecution.STATUS_CANCELLED)
        self.assertEqual(execution.output, '')
        self.assertEqual(provider.cancel_statuses, [202, 202])
        self.assertFalse(Artifact.objects.filter(project=self.project).exists())

    def test_queued_run_can_be_cancelled_by_owner(self):
        response = self._logged_client().post(f'/api/v1/projects/{self.project.pk}/runs/{self.run.pk}/cancel/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], ProjectRun.STATUS_CANCELLED)
        self.run.refresh_from_db()
        self.assertEqual(self.run.status, ProjectRun.STATUS_CANCELLED)

    def test_regeneration_keeps_previous_artifact_and_creates_new_version(self):
        original = process_run(self.run.pk, FakePlanningProvider())
        new_message = Message.objects.create(conversation=self.conversation, role=Message.ROLE_USER,
                                             content='Build an inventory tracker with history.')
        response = self._logged_client().post(
            f'/api/v1/projects/{self.project.pk}/runs/{original.pk}/regenerate/',
            data=json.dumps({'source_message_id': new_message.pk, 'feedback': 'Add a history screen.'}),
            content_type='application/json', HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )
        self.assertEqual(response.status_code, 202)
        regenerated = process_run(response.json()['id'], FakePlanningProvider())
        artifacts = list(Artifact.objects.filter(project=self.project).order_by('version'))
        self.assertEqual([item.version for item in artifacts], ['1', '2'])
        self.assertEqual(regenerated.previous_run_id, original.pk)
        self.assertEqual(original.status, ProjectRun.STATUS_SUCCEEDED)

    def test_owner_end_to_end_project_run_artifact_reflection_and_access_boundary(self):
        client = self._logged_client()
        created = client.post(
            '/api/v1/projects/',
            data=json.dumps({'title': 'E2E launch plan', 'summary': 'Day 19 acceptance',
                             'initial_message': 'Create a launch plan\nInclude milestone tracking and owner assignment.'}),
            content_type='application/json',
        )
        self.assertEqual(created.status_code, 201)
        project = created.json()['project']
        conversation = created.json()['conversation']
        source = created.json()['initial_message']
        submitted = client.post(
            f"/api/v1/projects/{project['id']}/runs/",
            data=json.dumps({'conversation_id': conversation['id'], 'source_message_id': source['id']}),
            content_type='application/json', HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )
        self.assertEqual(submitted.status_code, 202)
        run = process_run(submitted.json()['id'], FakePlanningProvider())
        self.assertEqual(run.status, ProjectRun.STATUS_SUCCEEDED)
        poll = client.get(f"/api/v1/projects/{project['id']}/runs/{run.pk}/")
        self.assertEqual(poll.json()['status'], ProjectRun.STATUS_SUCCEEDED)
        artifacts = client.get(f"/api/v1/projects/{project['id']}/artifacts/").json()['items']
        self.assertEqual(len(artifacts), 1)
        artifact_id = artifacts[0]['id']
        evaluated = client.post(f"/api/v1/projects/{project['id']}/artifacts/{artifact_id}/reflection/")
        self.assertEqual(evaluated.status_code, 201)
        self.assertEqual(evaluated.json()['run_id'], run.pk)
        detail_page = client.get(f"/projects/{project['id']}/")
        page_data = detail_page.content.decode('utf-8').split('<script id="sb-react-data" type="application/json">', 1)[1].split('</script>', 1)[0]
        detail_payload = json.loads(page_data)['data']['project']
        self.assertEqual(detail_payload['artifacts'][0]['id'], artifact_id)
        self.assertEqual(detail_payload['latest_reflection']['total_score'], evaluated.json()['total_score'])
        events = client.get(f"/api/v1/projects/{project['id']}/events/").json()['items']
        self.assertTrue(any(event['type'] == 'run.succeeded' for event in events))

        other = UserAccount.objects.create(identity_key='local:e2e-other@example.test', name='Other')
        other_client = Client()
        session = other_client.session
        session['sb_user'] = {'user_id': other.pk, 'role': 'user'}
        session.save()
        self.assertEqual(other_client.get(f"/api/v1/projects/{project['id']}/artifacts/").status_code, 404)
        self.assertEqual(other_client.get(f"/api/v1/projects/{project['id']}/artifacts/{artifact_id}/download/").status_code, 404)
