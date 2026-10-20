from django.test import TestCase
from django.urls import reverse


class SmokeTest(TestCase):
    def login(self, admin=False):
        self.client.post(reverse('accounts:login'), {'provider': 'google-admin' if admin else 'google'})

    def test_login_required_redirect(self):
        self.assertRedirects(self.client.get(reverse('dashboard:index')), reverse('accounts:login'))

    def test_login_screens_are_react_rendered(self):
        for url in [
            reverse('accounts:login'),
            reverse('accounts:demo_login'),
            reverse('accounts:face_auth'),
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertContains(response, 'id="root"')
            self.assertContains(response, 'id="sb-react-data"')
            if url == reverse('accounts:login'):
                self.assertContains(response, '/static/css/login.css')

    def test_demo_login(self):
        response = self.client.post(reverse('accounts:demo_login'), {'code': 'SECONDBRAIN'})
        self.assertRedirects(response, reverse('dashboard:index'))

    def test_dashboard_uses_react_and_preserves_shared_controls(self):
        self.client.post(reverse('accounts:demo_login'), {'code': 'SECONDBRAIN'})
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="root"')
        self.assertContains(response, '/static/react/assets/index-')
        self.assertContains(response, 'assets/index-')
        self.assertContains(response, 'screen-tour.js')
        self.assertContains(response, '/static/css/dashboard.css')
        self.assertContains(response, reverse('dashboard:faq'))

    def test_user_pages(self):
        self.login()
        for url in [
            reverse('dashboard:index'),
            reverse('projects:list'),
            reverse('projects:create'),
            reverse('projects:detail', args=[1]),
            reverse('comingsoon:index'),
            reverse('comingsoon:detail', args=['daily-briefing']),
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertContains(response, 'id="root"')
            self.assertContains(response, 'id="sb-react-data"')

    def test_admin_only_pages_blocked_for_user(self):
        self.login()
        self.assertRedirects(self.client.get(reverse('management:tasks')), reverse('comingsoon:blocked'))

    def test_admin_pages(self):
        self.login(admin=True)
        for url in [
            reverse('management:tasks'),
            reverse('management:agents'),
            reverse('management:agent_detail', args=['supervisor']),
            reverse('management:agent_detail', args=['engineering']),
            reverse('management:results'),
            reverse('comingsoon:manage'),
            reverse('comingsoon:editor_new'),
            reverse('comingsoon:editor', args=['daily-briefing']),
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertContains(response, 'id="root"')
            self.assertContains(response, 'id="sb-react-data"')

    def test_chat_reply(self):
        self.login()
        response = self.client.post(reverse('projects:chat_reply', args=[1]), {'message': '쇼핑몰 서비스를 기획해줘'})
        self.assertIn('Planning Agent', response.json()['reply'])
