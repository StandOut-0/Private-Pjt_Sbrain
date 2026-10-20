from django.test import TestCase
from django.urls import reverse


class NotificationsPageTest(TestCase):
    def test_notifications_requires_login(self):
        response = self.client.get(reverse('dashboard:notifications'))
        self.assertRedirects(response, reverse('accounts:login'))

    def test_notifications_page_contains_shared_demo_items(self):
        self.client.post(reverse('accounts:demo_login'), {'code': 'SECONDBRAIN'})
        response = self.client.get(reverse('dashboard:notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="root"')
        payload = response.context['sb_react_data']
        self.assertEqual(payload['page'], 'notifications')
        self.assertEqual(payload['links']['notifications'], '/notifications/')
        self.assertEqual(len(payload['notifications']), 3)


