import json

from django.test import Client, TestCase

from apps.accounts.models import UserAccount
from apps.reflection.models import QualityCriterion


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
