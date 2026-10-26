from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserAccount
from apps.execution.models import ExecutionEvent
from apps.projects.models import Project


class NotificationsPageTest(TestCase):
    def test_notifications_requires_login(self):
        response = self.client.get(reverse('dashboard:notifications'))
        self.assertRedirects(response, reverse('accounts:login'))

    def test_notifications_page_is_empty_without_project_run_events(self):
        self.client.post(reverse('accounts:demo_login'), {'code': 'SECONDBRAIN'})
        response = self.client.get(reverse('dashboard:notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="root"')
        payload = response.context['sb_react_data']
        self.assertEqual(payload['page'], 'notifications')
        self.assertEqual(payload['links']['notifications'], '/notifications/')
        self.assertEqual(payload['notifications'], [])

    def test_notifications_use_only_actual_events_from_owned_projects(self):
        self.client.post(reverse('accounts:demo_login'), {'code': 'SECONDBRAIN'})
        account = UserAccount.objects.get(pk=self.client.session['sb_user']['user_id'])
        project = Project.objects.create(owner=account, project_name='실제 작업 프로젝트')
        ExecutionEvent.objects.create(
            project=project,
            event_type='run.succeeded',
            message='Run completed',
        )
        other_user = UserAccount.objects.create(
            identity_key='test:other', email='other@example.com', name='Other'
        )
        other_project = Project.objects.create(owner=other_user, project_name='다른 사람의 프로젝트')
        ExecutionEvent.objects.create(
            project=other_project,
            event_type='run.failed',
            message='Run failed',
        )

        response = self.client.get(reverse('dashboard:notifications'))
        payload = response.context['sb_react_data']
        self.assertEqual(len(payload['notifications']), 1)
        self.assertEqual(payload['notifications'][0]['title'], '프로젝트 작업 완료')
        self.assertIn('실제 작업 프로젝트', payload['notifications'][0]['message'])
        self.assertEqual(payload['notifications'][0]['url'], f'/projects/{project.pk}/')


