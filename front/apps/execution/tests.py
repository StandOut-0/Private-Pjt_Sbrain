import json
import uuid

from django.core.management import call_command
from django.test import Client, TestCase, override_settings

from apps.accounts.models import UserAccount
from apps.execution.models import AgentExecution, ProjectRun, Task
from apps.execution.planning import FakePlanningProvider, PlanningError, process_run
from apps.artifacts.models import Artifact
from apps.projects.models import Conversation, Message, Project


class FailingProvider:
    def generate(self, request):
        raise PlanningError('PROVIDER_TIMEOUT', '기획 Provider 응답 시간이 초과됐습니다.', retryable=True)


class InvalidProvider:
    def generate(self, request):
        return {'title': 'incomplete'}


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
        self.assertEqual(json.loads(download.content), json.loads(artifact.content))

        other = UserAccount.objects.create(identity_key='local:other@example.test', name='Other')
        other_project = Project.objects.create(owner=other, project_name='Other project')
        denied = client.get(f'/api/v1/projects/{other_project.pk}/artifacts/')
        self.assertEqual(denied.status_code, 404)

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
