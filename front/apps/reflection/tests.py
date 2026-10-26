import json
import os
import unittest
from unittest.mock import patch

from django.contrib import admin
from django.test import Client, TestCase

from apps.accounts.models import UserAccount
from apps.reflection.models import QualityCriterion
from apps.reflection.evaluator import ReflectionError
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

    @patch('apps.reflection.evaluator._get_provider')
    def test_artifact_evaluation_persists_model_result_and_is_repeatable(self, get_provider):
        project = Project.objects.create(owner=self.user, project_name='Reflection project')
        conversation = Conversation.objects.create(project=project, owner=self.user)
        message = Message.objects.create(conversation=conversation, role='user', content='Build a task tracker')
        run = ProjectRun.objects.create(project=project, requested_by=self.user, conversation=conversation,
                                        source_message=message, idempotency_key='reflection-test')
        run = process_run(run.pk, FakePlanningProvider())
        artifact = run.planning_task.artifacts.get()
        provider = type('Provider', (), {
            'provider_name': 'ollama', 'model_name': 'gemma4:latest', 'last_usage': {},
            'evaluate': lambda self, content, criteria: {
                'summary': '요구사항과 완료 기준을 확인했습니다.',
                'criteria': [{'key': item['key'], 'score': 80, 'evidence': f"{item['label']} 항목 검토", 'deductions': []}
                             for item in criteria],
                'improvements': ['대상 사용자를 구체적으로 정하세요.'],
            },
        })()
        get_provider.return_value = provider
        response = self.user_client.post(f'/api/v1/projects/{project.pk}/artifacts/{artifact.pk}/reflection/')
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.json()['is_mock'])
        self.assertEqual(response.json()['run_id'], run.pk)
        self.assertEqual(sum(item['weight'] for item in response.json()['criteria_snapshot']), 100)
        self.assertIn('Ollama', response.json()['evaluation_label'])
        self.assertEqual(response.json()['total_score'], 80)
        self.assertEqual(response.json()['score_details'][0]['evidence'], f"{response.json()['score_details'][0]['label']} 항목 검토")
        again = self.user_client.post(f'/api/v1/projects/{project.pk}/artifacts/{artifact.pk}/reflection/')
        self.assertEqual(again.status_code, 200)
        fetched = self.user_client.get(f'/api/v1/projects/{project.pk}/artifacts/{artifact.pk}/reflection/')
        self.assertEqual(fetched.json()['id'], response.json()['id'])

    @patch('apps.reflection.evaluator._get_provider')
    def test_invalid_model_criteria_are_rejected_and_not_saved(self, get_provider):
        project = Project.objects.create(owner=self.user, project_name='Bad reflection project')
        conversation = Conversation.objects.create(project=project, owner=self.user)
        message = Message.objects.create(conversation=conversation, role='user', content='Build a task tracker')
        run = ProjectRun.objects.create(project=project, requested_by=self.user, conversation=conversation,
                                        source_message=message, idempotency_key='reflection-invalid-test')
        run = process_run(run.pk, FakePlanningProvider())
        artifact = run.planning_task.artifacts.get()
        provider = type('Provider', (), {
            'model_name': 'gemma4:latest', 'last_usage': {},
            'evaluate': lambda self, content, criteria: {
                'summary': '잘못된 결과', 'criteria': [{'key': [], 'score': 101, 'evidence': 'x', 'deductions': []}],
                'improvements': [],
            },
        })()
        get_provider.return_value = provider
        response = self.user_client.post(f'/api/v1/projects/{project.pk}/artifacts/{artifact.pk}/reflection/')
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['error']['code'], 'INVALID_PROVIDER_OUTPUT')
        from apps.reflection.models import ReflectionReport
        self.assertFalse(ReflectionReport.objects.filter(artifact=artifact).exists())

    @patch('apps.reflection.evaluator._get_provider', side_effect=ReflectionError('OLLAMA_UNAVAILABLE', 'Ollama가 실행 중인지 확인한 뒤 다시 시도해주세요.', retryable=True))
    def test_provider_failure_returns_retryable_error_without_mock_score(self, _get_provider):
        project = Project.objects.create(owner=self.user, project_name='Unavailable reflection project')
        conversation = Conversation.objects.create(project=project, owner=self.user)
        message = Message.objects.create(conversation=conversation, role='user', content='Build a task tracker')
        run = ProjectRun.objects.create(project=project, requested_by=self.user, conversation=conversation,
                                        source_message=message, idempotency_key='reflection-unavailable-test')
        run = process_run(run.pk, FakePlanningProvider())
        artifact = run.planning_task.artifacts.get()
        response = self.user_client.post(f'/api/v1/projects/{project.pk}/artifacts/{artifact.pk}/reflection/')
        self.assertEqual(response.status_code, 503)
        self.assertTrue(response.json()['error']['details']['retryable'])

    @unittest.skipUnless(os.environ.get('RUN_LOCAL_LLM_TEST') == '1', 'set RUN_LOCAL_LLM_TEST=1 to call local Ollama')
    def test_live_local_ollama_reflection_creates_non_mock_report(self):
        from apps.reflection.evaluator import evaluate_artifact
        project = Project.objects.create(owner=self.user, project_name='Live reflection project')
        conversation = Conversation.objects.create(project=project, owner=self.user)
        message = Message.objects.create(conversation=conversation, role='user', content='온라인 반려동물 사료 쇼핑몰을 기획하고 싶다. 고객이 사료를 비교하고 주문할 수 있어야 한다.')
        run = ProjectRun.objects.create(project=project, requested_by=self.user, conversation=conversation,
                                        source_message=message, idempotency_key='reflection-live-test')
        run = process_run(run.pk, FakePlanningProvider())
        artifact = run.planning_task.artifacts.get()
        report, created = evaluate_artifact(artifact)
        self.assertTrue(created)
        self.assertFalse(report.is_mock)
        self.assertEqual(len(report.score_details), 4)
        self.assertGreaterEqual(report.total_score, 0)
        self.assertLessEqual(report.total_score, 100)
