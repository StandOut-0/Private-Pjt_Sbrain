from django.test import Client, TestCase

from apps.accounts.models import UserAccount
from apps.execution.models import ProjectRun
from apps.execution.planning import FakePlanningProvider, process_run
from apps.projects.models import Conversation, Message, Project


class AdminExecutionObservabilityTests(TestCase):
    def setUp(self):
        self.owner = UserAccount.objects.create(identity_key='local:ops-owner@example.test', name='Owner')
        self.admin = UserAccount.objects.create(identity_key='local:ops-admin@example.test', name='Admin', role='admin')
        self.project = Project.objects.create(owner=self.owner, project_name='Observed project')
        conversation = Conversation.objects.create(project=self.project, owner=self.owner)
        message = Message.objects.create(conversation=conversation, role='user', content='Make a project plan')
        run = ProjectRun.objects.create(project=self.project, requested_by=self.owner, conversation=conversation,
                                        source_message=message, idempotency_key='ops-observability')
        process_run(run.pk, FakePlanningProvider())

    def _admin_client(self):
        client = Client()
        session = client.session
        session['sb_user'] = {'user_id': self.admin.pk, 'role': 'admin', 'is_admin': True}
        session.save()
        return client

    def test_admin_task_view_uses_database_execution_and_unmetered_values(self):
        response = self._admin_client().get('/manage/tasks/?status=done&q=PRD')
        self.assertEqual(response.status_code, 200)
        body = response.content.decode('utf-8').split('<script id="sb-react-data" type="application/json">', 1)[1].split('</script>', 1)[0]
        payload = json.loads(body)
        self.assertEqual(payload['data']['tasks'][0]['project'], 'Observed project')
        self.assertEqual(payload['data']['tasks'][0]['provider'], 'fake')
        self.assertEqual(payload['data']['tasks'][0]['model'], 'unmetered')
        self.assertIsNone(payload['data']['tasks'][0]['input_tokens'])

    def test_admin_task_view_filters_database_records(self):
        response = self._admin_client().get('/manage/tasks/?status=failed')
        self.assertEqual(response.status_code, 200)
        body = response.content.decode('utf-8').split('<script id="sb-react-data" type="application/json">', 1)[1].split('</script>', 1)[0]
        self.assertEqual(json.loads(body)['data']['tasks'], [])


import json

