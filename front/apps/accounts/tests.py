from django.test import TestCase
from django.urls import reverse


class SmokeTest(TestCase):
    def login(self, admin=False):
        self.client.post(reverse('accounts:login'), {'provider': 'google-admin' if admin else 'google'})

    def test_login_required_redirect(self):
        self.assertRedirects(self.client.get(reverse('dashboard:index')), reverse('accounts:login'))

    def test_demo_login(self):
        response = self.client.post(reverse('accounts:demo_login'), {'code': 'SECONDBRAIN'})
        self.assertRedirects(response, reverse('dashboard:index'))

    def test_user_pages(self):
        self.login()
        for url in [
            reverse('dashboard:index'),
            reverse('projects:list'),
            reverse('projects:create'),
            reverse('projects:detail', args=[1]),
            reverse('comingsoon:index'),
            reverse('comingsoon:detail', args=['mcp-tool-extension']),
        ]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

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
            reverse('comingsoon:editor', args=['mcp-tool-extension']),
        ]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_chat_reply(self):
        self.login()
        response = self.client.post(reverse('projects:chat_reply', args=[1]), {'message': '쇼핑몰 서비스를 기획해줘'})
        self.assertIn('Planning Agent', response.json()['reply'])
