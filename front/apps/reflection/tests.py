import json

from django.contrib import admin
from django.test import Client, TestCase

from apps.accounts.models import UserAccount
from apps.reflection.models import QualityCriterion
from apps.execution.models import ProjectRun
from apps.execution.planning import FakePlanningProvider, process_run
from apps.projects.models import Conversation, Message, Project


class QualityCriterionTests(TestCase):
    def setUp(self):
        self.admin = UserAccount.objects.create(identity_key='local:criteria-admin@example.test', name='Admin', role='admin')
        self.user = UserAccount.objects.create(identity_key='local:criteria-user@example.test', name='User')
        self.admin_client = self._client(self.admin)
        self.user_client = self._client(self.user)

    def _client(self, account):
        client = Client()
        session = client.session
        session['sb_user'] = {'user_id': account.pk, 'role': account.role}
        session.save()
        return client

    def test_seeded_criteria_sum_to_100(self):
        response = self.admin_client.get('/api/v1/quality-criteria/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total_weight'], 100)
        self.assertEqual(QualityCriterion.objects.filter(is_active=True).count(), 4)

    def test_user_cannot_replace_criteria(self):
        response = self.user_client.post('/api/v1/quality-criteria/replace/', data='{}', content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_admin_replace_requires_active_weight_sum_100(self):
        items = [
            {'key': 'new-a', 'label': 'A', 'description': '', 'weight': 60, 'is_active': True, 'sort_order': 1},
            {'key': 'new-b', 'label': 'B', 'description': '', 'weight': 40, 'is_active': True, 'sort_order': 2},
        ]
        response = self.admin_client.post('/api/v1/quality-criteria/replace/', data=json.dumps({'items': items}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total_weight'], 100)
        items[1]['weight'] = 39
        rejected = self.admin_client.post('/api/v1/quality-criteria/replace/', data=json.dumps({'items': items}), content_type='application/json')
        self.assertEqual(rejected.status_code, 422)
        self.assertEqual(rejected.json()['error']['code'], 'WEIGHT_SUM_INVALID')
        self.assertEqual(sum(QualityCriterion.objects.filter(is_active=True).values_list('weight', flat=True)), 100)

    def test_invalid_criterion_fields_are_rejected_without_changing_existing_values(self):
        invalid_items = [
            {'key': 'bad key', 'label': 'A', 'description': '', 'weight': 100, 'is_active': True, 'sort_order': 0},
            {'key': 'bad-order', 'label': 'A', 'description': '', 'weight': 100, 'is_active': True, 'sort_order': -1},
            {'key': 'blank-label', 'label': ' ', 'description': '', 'weight': 100, 'is_active': True, 'sort_order': 0},
        ]
        before = list(QualityCriterion.objects.values_list('key', 'weight'))
        for items in invalid_items:
            response = self.admin_client.post('/api/v1/quality-criteria/replace/',
                                              data=json.dumps({'items': items}), content_type='application/json')
            self.assertEqual(response.status_code, 422)
            self.assertEqual(response.json()['error']['code'], 'VALIDATION_ERROR')
            self.assertEqual(list(QualityCriterion.objects.values_list('key', 'weight')), before)

    def test_criterion_admin_is_read_only(self):
        model_admin = admin.site._registry[QualityCriterion]
        request = type('Request', (), {})()
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_delete_permission(request))
        self.assertIn('weight', model_admin.get_readonly_fields(request))

    def test_artifact_evaluation_persists_criteria_snapshot_and_is_repeatable(self):
        project = Project.objects.create(owner=self.user, project_name='Reflection project')
        conversation = Conversation.objects.create(project=project, owner=self.user)
        message = Message.objects.create(conversation=conversation, role='user', content='Build a task tracker')
        run = ProjectRun.objects.create(project=project, requested_by=self.user, conversation=conversation,
                                        source_message=message, idempotency_key='reflection-test')
        run = process_run(run.pk, FakePlanningProvider())
        artifact = run.planning_task.artifacts.get()
        response = self.user_client.post(f'/api/v1/projects/{project.pk}/artifacts/{artifact.pk}/reflection/')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['is_mock'])
        self.assertEqual(response.json()['run_id'], run.pk)
        self.assertEqual(sum(item['weight'] for item in response.json()['criteria_snapshot']), 100)
        self.assertIn('mock', response.json()['evaluation_label'])
        again = self.user_client.post(f'/api/v1/projects/{project.pk}/artifacts/{artifact.pk}/reflection/')
        self.assertEqual(again.status_code, 200)
        fetched = self.user_client.get(f'/api/v1/projects/{project.pk}/artifacts/{artifact.pk}/reflection/')
        self.assertEqual(fetched.json()['id'], response.json()['id'])
