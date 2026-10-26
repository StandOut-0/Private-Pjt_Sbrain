import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import UserAccount
from apps.artifacts.models import Artifact
from apps.execution.models import ProjectRun
from apps.execution.models import AgentExecution
from apps.execution.planning import FakePlanningProvider, process_run
from apps.management.models import KnowledgeDocument
from apps.management.retrieval import retrieve_knowledge
from apps.projects.models import Conversation, Message, Project


class AdminExecutionObservabilityTests(TestCase):
    def setUp(self):
        self.owner = UserAccount.objects.create(identity_key='local:ops-owner@example.test', name='Owner')
        self.admin = UserAccount.objects.create(identity_key='local:ops-admin@example.test', name='Admin', role='admin')
        self.project = Project.objects.create(owner=self.owner, project_name='Observed project')
        conversation = Conversation.objects.create(project=self.project, owner=self.owner)
        message = Message.objects.create(conversation=conversation, role='user', content='Make a project plan')
        run = ProjectRun.objects.create(project=self.project, requested_by=self.owner, conversation=conversation,
                                        source_message=message, idempotency_key='ops-observability')
        process_run(run.pk, FakePlanningProvider())

    def _admin_client(self):
        client = Client()
        session = client.session
        session['sb_user'] = {'user_id': self.admin.pk, 'role': 'admin', 'is_admin': True}
        session.save()
        return client

    def test_admin_task_view_uses_database_execution_and_unmetered_values(self):
        response = self._admin_client().get('/manage/tasks/?status=done&q=PRD')
        self.assertEqual(response.status_code, 200)
        body = response.content.decode('utf-8').split('<script id="sb-react-data" type="application/json">', 1)[1].split('</script>', 1)[0]
        payload = json.loads(body)
        self.assertEqual(payload['data']['tasks'][0]['project'], 'Observed project')
        self.assertEqual(payload['data']['tasks'][0]['provider'], 'fake')
        self.assertEqual(payload['data']['tasks'][0]['model'], 'unmetered')
        self.assertIsNone(payload['data']['tasks'][0]['input_tokens'])

    def test_admin_task_view_filters_database_records(self):
        response = self._admin_client().get('/manage/tasks/?status=failed')
        self.assertEqual(response.status_code, 200)
        body = response.content.decode('utf-8').split('<script id="sb-react-data" type="application/json">', 1)[1].split('</script>', 1)[0]
        self.assertEqual(json.loads(body)['data']['tasks'], [])

    def test_admin_results_reads_persisted_artifacts_and_downloads_zip(self):
        client = self._admin_client()
        response = client.get(reverse('management:results'))
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content.decode('utf-8').split(
            '<script id="sb-react-data" type="application/json">', 1
        )[1].split('</script>', 1)[0])
        tree = payload['data']['tree']
        artifact = self.project.artifacts.get()
        self.assertEqual(tree[0]['name'], self.project.project_name)
        self.assertEqual(tree[0]['files'][0]['id'], artifact.pk)
        self.assertIn('/artifacts/', tree[0]['files'][0]['detail_url'])

        zipped = client.get(reverse('management:download_results_zip'), {'project': self.project.pk})
        self.assertEqual(zipped.status_code, 200)
        self.assertEqual(zipped['Content-Type'], 'application/zip')
        self.assertGreater(len(zipped.content), 30)

    def test_knowledge_upload_is_persisted_and_not_claimed_as_indexed(self):
        client = self._admin_client()
        response = client.post(reverse('management:results') + '?tab=knowledge', {
            'action': 'knowledge-upload',
            'scope': 'project',
            'project': str(self.project.pk),
            'file': SimpleUploadedFile('guide.md', b'# First guide\nSaved text', content_type='text/markdown'),
        })
        self.assertRedirects(response, '/manage/results/?tab=knowledge&uploaded=1')
        document = KnowledgeDocument.objects.get()
        self.assertEqual(document.project, self.project)
        self.assertEqual(document.content, '# First guide\nSaved text')

        response = client.get('/manage/results/?tab=knowledge&rag_q=guide')
        payload = json.loads(response.content.decode('utf-8').split(
            '<script id="sb-react-data" type="application/json">', 1
        )[1].split('</script>', 1)[0])
        self.assertEqual(payload['data']['vector_documents'][0]['status'], '키워드 검색 가능 · 벡터 미색인')
        self.assertEqual(payload['data']['knowledge_stats'][0]['value'], 1)

    def test_admin_can_read_artifact_from_any_project_but_user_cannot(self):
        artifact = self.project.artifacts.get()
        detail_url = f'/api/v1/projects/{self.project.pk}/artifacts/{artifact.pk}/'
        self.assertEqual(self._admin_client().get(detail_url).status_code, 200)

        owner_client = Client()
        session = owner_client.session
        session['sb_user'] = {'user_id': self.owner.pk, 'role': 'user', 'is_admin': False}
        session.save()
        other = UserAccount.objects.create(identity_key='local:other-owner@example.test', name='Other')
        # The authenticated owner can see the project artifact; unrelated accounts stay blocked.
        self.assertEqual(owner_client.get(detail_url).status_code, 200)
        other_client = Client()
        session = other_client.session
        session['sb_user'] = {'user_id': other.pk, 'role': 'user', 'is_admin': False}
        session.save()
        self.assertEqual(other_client.get(detail_url).status_code, 404)

    def test_agent_status_and_metrics_reflect_real_executions(self):
        response = self._admin_client().get(reverse('management:agents'))
        payload = json.loads(response.content.decode('utf-8').split(
            '<script id="sb-react-data" type="application/json">', 1
        )[1].split('</script>', 1)[0])['data']
        agents = {agent['key']: agent for agent in payload['workers']}
        self.assertEqual(agents['planning']['status'], 'done')
        self.assertEqual(agents['planning']['metrics'][0]['value'], '1')
        self.assertEqual(agents['creative']['status_label'], '미실행')
        self.assertEqual(agents['creative']['metrics'][0]['value'], '0')

        detail = self._admin_client().get(reverse('management:agent_detail', args=['creative']))
        detail_payload = json.loads(detail.content.decode('utf-8').split(
            '<script id="sb-react-data" type="application/json">', 1
        )[1].split('</script>', 1)[0])['data']
        self.assertEqual(detail_payload['agent']['project'], '실행 이력 없음')

    def test_reflection_agent_page_loads_saved_quality_criteria_for_editor(self):
        response = self._admin_client().get(reverse('management:agent_detail', args=['reflection']))
        payload = json.loads(response.content.decode('utf-8').split(
            '<script id="sb-react-data" type="application/json">', 1
        )[1].split('</script>', 1)[0])['data']
        self.assertTrue(payload['criteria'])
        self.assertEqual(sum(item['weight'] for item in payload['criteria'] if item['is_active']), 100)

    def test_knowledge_retrieval_scopes_global_and_project_documents(self):
        global_doc = KnowledgeDocument.objects.create(
            title='Clinic portal basics', original_name='global.md', scope=KnowledgeDocument.SCOPE_GLOBAL,
            content='Clinic portal requires appointment scheduling.', uploaded_by=self.admin,
        )
        project_doc = KnowledgeDocument.objects.create(
            title='Clinic booking requirements', original_name='local.md', scope=KnowledgeDocument.SCOPE_PROJECT,
            project=self.project, content='The clinic booking portal needs confirmation.', uploaded_by=self.admin,
        )
        another_project = Project.objects.create(owner=self.owner, project_name='Another')
        KnowledgeDocument.objects.create(
            title='Clinic private notes', original_name='private.md', scope=KnowledgeDocument.SCOPE_PROJECT,
            project=another_project, content='Clinic portal private notes.', uploaded_by=self.admin,
        )

        references = retrieve_knowledge(self.project.pk, {'objective': 'Build a clinic booking portal'})

        self.assertEqual({item['document_id'] for item in references}, {global_doc.pk, project_doc.pk})
        self.assertEqual(references[0]['title'], project_doc.title)

    def test_planning_execution_receives_relevant_knowledge_context(self):
        KnowledgeDocument.objects.create(
            title='Clinic booking requirements', original_name='clinic.md',
            scope=KnowledgeDocument.SCOPE_PROJECT, project=self.project,
            content='Clinic booking needs appointment confirmation and reminders.', uploaded_by=self.admin,
        )
        conversation = Conversation.objects.create(project=self.project, owner=self.owner)
        message = Message.objects.create(
            conversation=conversation, role='user', content='Build a clinic booking portal with reminders',
        )
        run = ProjectRun.objects.create(
            project=self.project, requested_by=self.owner, conversation=conversation,
            source_message=message, idempotency_key='knowledge-context-run',
        )

        process_run(run.pk, FakePlanningProvider())

        run.refresh_from_db()
        execution = run.planning_task.executions.get()
        saved_input = json.loads(execution.input)
        artifact = self.project.artifacts.get(agent_execution__task__run=run)
        artifact_body = json.loads(artifact.content)
        self.assertEqual(run.status, ProjectRun.STATUS_SUCCEEDED)
        self.assertEqual(saved_input['knowledge_context'][0]['title'], 'Clinic booking requirements')
        self.assertIn('appointment confirmation', saved_input['knowledge_context'][0]['excerpt'])
        self.assertEqual(artifact_body['knowledge_sources'][0]['title'], 'Clinic booking requirements')

