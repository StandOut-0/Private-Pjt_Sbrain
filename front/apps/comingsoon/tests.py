import shutil
import json
import re
import uuid
from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.comingsoon import storage


class ComingSoonFlowTests(TestCase):
    def setUp(self):
        self.temp_dir = Path(settings.BASE_DIR) / 'tmp' / ('comingsoon-tests-' + uuid.uuid4().hex)
        self.temp_dir.mkdir(parents=True)
        root = self.temp_dir
        self.docs_dir = root / 'docs'
        self.deleted_dir = root / 'deleted'
        self.settings_override = override_settings(
            COMING_SOON_DIR=self.docs_dir,
            COMING_SOON_DELETED_DIR=self.deleted_dir,
        )
        self.settings_override.enable()
        self.client.post(reverse('accounts:login'), {'provider': 'google-admin'})

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_document_metadata_parsing_and_filters(self):
        storage.save_document(None, {
            'title': 'MCP Tools', 'summary': 'MCP 기반 도구', 'status': '연구 예정',
            'category': 'Agent', 'technologies': 'MCP, API', 'related_agents': 'Supervisor',
        }, '# 목적\n테스트')
        document = storage.read_document('mcp-tools')
        self.assertEqual(document['technologies'], ['MCP', 'API'])
        self.assertEqual(len(storage.list_documents(status='연구 예정', category='Agent')), 1)

    def test_admin_can_create_edit_and_soft_delete_document(self):
        create_url = reverse('comingsoon:editor_new')
        response = self.client.post(create_url, {
            'title': '새 아이디어', 'summary': '기능 요약', 'status': '아이디어',
            'category': 'Agent', 'technologies': 'React, Django',
            'related_agents': 'Engineering', 'body': '# 목적\n본문',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue((self.docs_dir / '새-아이디어.md').exists())

        edit_url = reverse('comingsoon:editor', args=['새-아이디어'])
        response = self.client.post(edit_url, {
            'title': '새 아이디어', 'summary': '수정된 설명', 'status': '개발 예정',
            'category': 'Engineering', 'technologies': 'React',
            'related_agents': 'Frontend', 'body': '# 수정됨',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(storage.read_document('새-아이디어')['summary'], '수정된 설명')

        response = self.client.post(reverse('comingsoon:delete', args=['새-아이디어']))
        self.assertEqual(response.status_code, 302)
        self.assertFalse((self.docs_dir / '새-아이디어.md').exists())
        self.assertEqual(len(list(self.deleted_dir.glob('새-아이디어-*.md'))), 1)

    def test_invalid_input_renders_form_error_without_writing_file(self):
        response = self.client.post(reverse('comingsoon:editor_new'), {
            'title': 'invalid/title', 'summary': '', 'status': '아이디어',
            'category': 'Agent', 'body': 'draft',
        })
        self.assertEqual(response.status_code, 400)
        payload_tag = re.search(rb'<script id="sb-react-data" type="application/json">(.*?)</script>', response.content)
        self.assertIsNotNone(payload_tag)
        payload = json.loads(payload_tag.group(1))
        self.assertIn('URL에서 사용할 수 없는', payload['data']['error'])
        self.assertEqual(list(self.docs_dir.glob('*.md')), [])

    def test_admin_filters_and_public_detail(self):
        storage.save_document(None, {
            'title': '데일리 요약', 'summary': '매일 브리핑', 'status': '연구 예정',
            'category': 'Data', 'technologies': [], 'related_agents': [],
        }, '# 브리핑')
        response = self.client.get(reverse('comingsoon:manage'), {'q': '브리핑', 'status': '연구 예정', 'category': 'Data'})
        self.assertEqual(response.status_code, 200)
        payload_tag = re.search(rb'<script id="sb-react-data" type="application/json">(.*?)</script>', response.content)
        self.assertIsNotNone(payload_tag)
        payload = json.loads(payload_tag.group(1))
        self.assertEqual(payload['page'], 'comingsoon-manage')
        self.assertEqual(payload['data']['documents'][0]['title'], '데일리 요약')
        self.assertEqual(self.client.get(reverse('comingsoon:detail', args=['데일리-요약'])).status_code, 200)
