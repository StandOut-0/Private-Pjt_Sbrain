from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import AdminFacePhoto, UserAccount
from apps.projects.models import Project
from apps.projects.models import Conversation, Message


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
        session_user = self.client.session['sb_user']
        account = UserAccount.objects.get(pk=session_user['user_id'])
        self.assertEqual(session_user['role'], 'demo')
        self.assertEqual(account.role, UserAccount.ROLE_USER)
        self.assertIsNone(account.email)
        self.assertTrue(account.identity_key.startswith('demo-guest:'))

    def test_demo_sessions_receive_separate_persistent_owners(self):
        first = self.client
        first.post(reverse('accounts:demo_login'), {'code': 'SECONDBRAIN'})
        first_identity = first.session['sb_user']['user_id']

        second = self.client_class()
        second.post(reverse('accounts:demo_login'), {'code': 'SECONDBRAIN'})
        second_identity = second.session['sb_user']['user_id']

        self.assertNotEqual(first_identity, second_identity)

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
        account = UserAccount.objects.get(pk=self.client.session['sb_user']['user_id'])
        project = Project.objects.create(owner=account, project_name='Private test project')
        for url in [
            reverse('dashboard:index'),
            reverse('projects:list'),
            reverse('projects:detail', args=[project.pk]),
            reverse('comingsoon:index'),
            reverse('comingsoon:detail', args=['daily-briefing']),
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertContains(response, 'id="root"')
            self.assertContains(response, 'id="sb-react-data"')

    def test_project_create_route_redirects_to_popup_entry_page(self):
        self.login()
        self.assertRedirects(
            self.client.get(reverse('projects:create')),
            reverse('projects:list'),
        )

    def test_admin_only_pages_blocked_for_user(self):
        self.login()
        self.assertRedirects(self.client.get(reverse('management:tasks')), reverse('comingsoon:blocked'))

    def test_admin_access_uses_persisted_role_not_session_flag(self):
        self.login()
        session = self.client.session
        session_user = session['sb_user']
        session_user['role'] = 'admin'
        session_user['is_admin'] = True
        session['sb_user'] = session_user
        session.save()

        self.assertRedirects(
            self.client.get(reverse('management:tasks')),
            reverse('comingsoon:blocked'),
        )

    def test_admin_pages(self):
        self.login(admin=True)
        for url in [
            reverse('management:tasks'),
            reverse('management:agents'),
            reverse('management:agent_detail', args=['supervisor']),
            reverse('management:agent_detail', args=['engineering']),
            reverse('management:results'),
            reverse('management:face_photo'),
            reverse('comingsoon:manage'),
            reverse('comingsoon:editor_new'),
            reverse('comingsoon:editor', args=['daily-briefing']),
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertContains(response, 'id="root"')
            self.assertContains(response, 'id="sb-react-data"')

    def test_admin_face_photo_is_private_and_can_be_enrolled_replaced_and_removed(self):
        self.login(admin=True)
        url = reverse('management:face_photo')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['sb_react_data']['data']['face_photo'])

        image = SimpleUploadedFile('admin.png', b'\x89PNG\r\n\x1a\nsmall-test-image', content_type='image/png')
        response = self.client.post(url, {'photo': image})
        self.assertRedirects(response, f'{url}?saved=1')
        account = UserAccount.objects.get(pk=self.client.session['sb_user']['user_id'])
        self.assertEqual(account.face_photo.content_type, 'image/png')
        self.assertEqual(bytes(account.face_photo.image_data), b'\x89PNG\r\n\x1a\nsmall-test-image')
        response = self.client.get(url)
        self.assertTrue(response.context['sb_react_data']['data']['face_photo']['data_url'].startswith('data:image/png;base64,'))

        replacement = SimpleUploadedFile('admin.webp', b'RIFFabcdWEBPtest', content_type='image/webp')
        self.client.post(url, {'photo': replacement})
        account.face_photo.refresh_from_db()
        self.assertEqual(account.face_photo.content_type, 'image/webp')

        self.client.post(url, {'action': 'delete'})
        self.assertFalse(AdminFacePhoto.objects.filter(account=account).exists())

    def test_admin_face_photo_rejects_users_and_invalid_images(self):
        url = reverse('management:face_photo')
        self.login()
        self.assertRedirects(self.client.get(url), reverse('comingsoon:blocked'))

        self.client.post(reverse('accounts:logout'))
        self.login(admin=True)
        invalid = SimpleUploadedFile('not-image.txt', b'not an image', content_type='text/plain')
        response = self.client.post(url, {'photo': invalid})
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'JPEG, PNG, WEBP', status_code=400)

    def test_chat_reply(self):
        self.login()
        account = UserAccount.objects.get(pk=self.client.session['sb_user']['user_id'])
        project = Project.objects.create(owner=account, project_name='Test shop')
        conversation = Conversation.objects.create(project=project, owner=account, title='Test chat')
        response = self.client.post(reverse('projects:chat_reply', args=[project.pk]), {
            'message': '쇼핑몰 서비스를 기획해줘',
            'conversation_id': conversation.pk,
        })
        self.assertIn('Planning Agent', response.json()['reply'])
        self.assertEqual(conversation.messages.filter(role=Message.ROLE_ASSISTANT).count(), 1)
