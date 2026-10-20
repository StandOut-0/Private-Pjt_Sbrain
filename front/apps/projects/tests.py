from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import UserAccount
from apps.projects.models import Project


class ProjectOwnershipTests(TestCase):
    def setUp(self):
        self.owner = UserAccount.objects.create(
            identity_key='local:owner@example.test',
            name='Owner',
            email='owner@example.test',
        )
        self.other = UserAccount.objects.create(
            identity_key='local:other@example.test',
            name='Other',
            email='other@example.test',
        )
        self.project = Project.objects.create(
            owner=self.owner,
            project_name='Owner private project',
            description='Private data',
        )

    def _client_for(self, account):
        client = Client()
        session = client.session
        session['sb_user'] = {
            'user_id': account.pk,
            'name': account.name,
            'role': account.role,
            'email': account.email or '',
            'role_label': '사용자',
            'is_admin': account.role == UserAccount.ROLE_ADMIN,
        }
        session.save()
        return client

    def test_owner_can_read_project_page_and_api(self):
        client = self._client_for(self.owner)

        page_response = client.get(reverse('projects:detail', args=[self.project.pk]))
        api_response = client.get(reverse('project_api:project_detail', args=[self.project.pk]))

        self.assertEqual(page_response.status_code, 200)
        self.assertEqual(api_response.status_code, 200)
        self.assertEqual(api_response.json()['id'], self.project.pk)
        self.assertEqual(api_response.json()['title'], 'Owner private project')

    def test_other_user_cannot_read_project_page_or_api(self):
        client = self._client_for(self.other)

        page_response = client.get(reverse('projects:detail', args=[self.project.pk]))
        api_response = client.get(reverse('project_api:project_detail', args=[self.project.pk]))

        self.assertEqual(page_response.status_code, 404)
        self.assertEqual(api_response.status_code, 404)
        self.assertEqual(api_response.json()['error']['code'], 'PROJECT_NOT_FOUND')

    def test_project_api_uses_json_auth_error(self):
        response = Client().get(reverse('project_api:project_detail', args=[self.project.pk]))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error']['code'], 'AUTH_REQUIRED')
