import json

from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import UserAccount
from apps.execution.models import ProjectRun
from apps.execution.models import Task
from apps.projects.models import Conversation, Message, Project


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

    def test_project_list_filters_only_owned_database_projects(self):
        Project.objects.create(owner=self.other, project_name='Hidden project')
        Project.objects.create(owner=self.owner, project_name='Another project', status=Project.STATUS_COMPLETED)
        client = self._client_for(self.owner)

        response = client.get(reverse('projects:list'), {'project_q': 'Another', 'project_status': 'done'})

        self.assertEqual(response.status_code, 200)
        payload = response.context['sb_react_data']['data']
        self.assertEqual([project['title'] for project in payload['projects']], ['Another project'])
        self.assertEqual(payload['total_projects'], 2)
        self.assertEqual(payload['filters']['status'], 'done')

    def test_modal_project_create_persists_project_and_initial_goal(self):
        client = self._client_for(self.owner)

        response = client.post(reverse('projects:create'), {
            'title': 'New product',
            'summary': 'A small summary',
            'goal': 'Plan the first release.',
        })

        project = Project.objects.get(project_name='New product')
        self.assertRedirects(response, reverse('projects:detail', args=[project.pk]))
        self.assertEqual(project.owner_id, self.owner.pk)
        conversation = Conversation.objects.get(project=project)
        message = Message.objects.get(conversation=conversation)
        self.assertEqual(conversation.owner_id, self.owner.pk)
        self.assertEqual(message.role, Message.ROLE_USER)
        self.assertEqual(message.content, 'Plan the first release.')

    def test_project_create_api_and_collection_are_owner_scoped(self):
        client = self._client_for(self.owner)
        create_response = client.post(
            reverse('project_api:project_collection'),
            data='{"title":"API project","summary":"","initial_message":"Start here"}',
            content_type='application/json',
        )

        self.assertEqual(create_response.status_code, 201)
        body = create_response.json()
        self.assertEqual(body['project']['title'], 'API project')
        self.assertEqual(body['conversation']['title'], 'API project')
        self.assertEqual(body['initial_message']['content'], 'Start here')
        Project.objects.create(owner=self.other, project_name='Private to other')
        listed = client.get(reverse('project_api:project_collection')).json()
        self.assertEqual([item['title'] for item in listed['items']], ['API project', 'Owner private project'])

    def test_project_create_api_rejects_invalid_title_and_status(self):
        client = self._client_for(self.owner)
        invalid_create = client.post(
            reverse('project_api:project_collection'),
            data='{"title":"x"}',
            content_type='application/json',
        )
        invalid_filter = client.get(reverse('project_api:project_collection'), {'status': 'unknown'})

        self.assertEqual(invalid_create.status_code, 422)
        self.assertEqual(invalid_create.json()['error']['code'], 'VALIDATION_ERROR')
        self.assertEqual(invalid_filter.status_code, 422)
        self.assertEqual(invalid_filter.json()['error']['code'], 'VALIDATION_ERROR')

    def test_project_api_updates_only_owned_projects(self):
        client = self._client_for(self.owner)
        response = client.patch(
            reverse('project_api:project_detail', args=[self.project.pk]),
            data='{"title":"Updated title","summary":"Updated summary","status":"completed"}',
            content_type='application/json',
        )
        denied = self._client_for(self.other).patch(
            reverse('project_api:project_detail', args=[self.project.pk]),
            data='{"title":"Attempted takeover"}',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], 'Updated title')
        self.assertEqual(response.json()['summary'], 'Updated summary')
        self.assertEqual(response.json()['status'], 'completed')
        self.project.refresh_from_db()
        self.assertEqual(self.project.project_name, 'Updated title')
        self.assertEqual(denied.status_code, 404)

    def test_dashboard_and_sidebar_only_include_projects_owned_by_current_account(self):
        Project.objects.create(owner=self.other, project_name='Other private project')
        client = self._client_for(self.owner)

        response = client.get(reverse('dashboard:index'))
        payload = response.context['sb_react_data']

        self.assertEqual([project['title'] for project in payload['data']['projects']], ['Owner private project'])
        self.assertEqual([project['title'] for project in payload['navProjects']], ['Owner private project'])

    def test_project_list_cursor_pages_consistently(self):
        for index in range(3):
            Project.objects.create(owner=self.owner, project_name=f'Page project {index}')
        client = self._client_for(self.owner)

        first = client.get(reverse('project_api:project_collection'), {'limit': 2}).json()
        second = client.get(reverse('project_api:project_collection'), {'limit': 2, 'cursor': first['next_cursor']}).json()

        self.assertEqual(len(first['items']), 2)
        self.assertIsNotNone(first['next_cursor'])
        self.assertEqual(len(second['items']), 2)
        self.assertIsNone(second['next_cursor'])
        self.assertTrue(set(item['id'] for item in first['items']).isdisjoint(item['id'] for item in second['items']))

    def test_conversation_and_messages_survive_repeated_reads(self):
        client = self._client_for(self.owner)
        conversation_url = reverse('project_api:conversation_collection', args=[self.project.pk])
        created = client.post(
            conversation_url,
            data='{"title":"Planning discussion"}',
            content_type='application/json',
        )
        conversation = created.json()
        messages_url = reverse(
            'project_api:conversation_messages',
            args=[self.project.pk, conversation['id']],
        )
        sent = client.post(
            messages_url,
            data='{"content":"  Define the first release.  "}',
            content_type='application/json',
        )

        self.assertEqual(created.status_code, 201)
        self.assertEqual(sent.status_code, 201)
        self.assertEqual(sent.json()['content'], 'Define the first release.')
        first_read = client.get(messages_url).json()
        refreshed_read = self._client_for(self.owner).get(messages_url).json()
        self.assertEqual(first_read, refreshed_read)
        self.assertEqual([message['content'] for message in refreshed_read['items']], ['Define the first release.'])
        self.assertEqual(refreshed_read['items'][0]['role'], Message.ROLE_USER)

    def test_conversation_message_apis_enforce_project_conversation_owner_chain(self):
        conversation = Conversation.objects.create(
            project=self.project,
            owner=self.owner,
            title='Private discussion',
        )
        client = self._client_for(self.other)
        collection = client.get(reverse('project_api:conversation_collection', args=[self.project.pk]))
        messages = client.get(reverse(
            'project_api:conversation_messages',
            args=[self.project.pk, conversation.pk],
        ))
        mismatched_project = self._client_for(self.owner).get(reverse(
            'project_api:conversation_messages',
            args=[Project.objects.create(owner=self.owner, project_name='Different project').pk, conversation.pk],
        ))

        self.assertEqual(collection.status_code, 404)
        self.assertEqual(messages.status_code, 404)
        self.assertEqual(messages.json()['error']['code'], 'CONVERSATION_NOT_FOUND')
        self.assertEqual(mismatched_project.status_code, 404)

    def test_message_validation_and_ascending_cursor_pagination(self):
        client = self._client_for(self.owner)
        conversation = Conversation.objects.create(project=self.project, owner=self.owner, title='Cursor test')
        messages_url = reverse('project_api:conversation_messages', args=[self.project.pk, conversation.pk])
        empty = client.post(messages_url, data='{"content":"   "}', content_type='application/json')
        for index in range(3):
            response = client.post(messages_url, data=f'{{"content":"message {index}"}}', content_type='application/json')
            self.assertEqual(response.status_code, 201)

        first = client.get(messages_url, {'limit': 2}).json()
        second = client.get(messages_url, {'limit': 2, 'cursor': first['next_cursor']}).json()

        self.assertEqual(empty.status_code, 422)
        self.assertEqual([item['content'] for item in first['items']], ['message 0', 'message 1'])
        self.assertEqual([item['content'] for item in second['items']], ['message 2'])
        self.assertIsNone(second['next_cursor'])

    def test_chat_reply_persists_server_assistant_response(self):
        client = self._client_for(self.owner)
        conversation = Conversation.objects.create(project=self.project, owner=self.owner, title='Existing chat')
        message_url = reverse('project_api:conversation_messages', args=[self.project.pk, conversation.pk])
        client.post(message_url, data='{"content":"쇼핑몰 서비스를 기획해줘"}', content_type='application/json')

        response = client.post(
            reverse('projects:chat_reply', args=[self.project.pk]),
            data=json.dumps({'message': '쇼핑몰 서비스를 기획해줘', 'conversation_id': conversation.pk}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['assistant_message']['role'], Message.ROLE_ASSISTANT)
        self.assertEqual(conversation.messages.count(), 2)

    def test_run_request_is_queued_and_idempotent(self):
        client = self._client_for(self.owner)
        conversation = Conversation.objects.create(project=self.project, owner=self.owner, title='Run request')
        source = Message.objects.create(conversation=conversation, role=Message.ROLE_USER, content='Create a PRD')
        url = reverse('project_api:run_collection', args=[self.project.pk])
        key = 'f7b2a101-c5cd-43d6-aea3-28b053a212df'
        body = {'conversation_id': conversation.pk, 'source_message_id': source.pk}
        first = client.post(url, data=json.dumps(body), content_type='application/json', HTTP_IDEMPOTENCY_KEY=key)
        duplicate = client.post(url, data=json.dumps(body), content_type='application/json', HTTP_IDEMPOTENCY_KEY=key)

        self.assertEqual(first.status_code, 202)
        self.assertEqual(first.json()['status'], ProjectRun.STATUS_QUEUED)
        self.assertEqual(first.json()['task']['status'], Task.STATUS_QUEUED)
        self.assertEqual(first['Location'], reverse('project_api:run_detail', args=[self.project.pk, first.json()['id']]))
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(duplicate.json()['id'], first.json()['id'])
        self.assertEqual(ProjectRun.objects.filter(project=self.project).count(), 1)
        task = ProjectRun.objects.get(pk=first.json()['id']).planning_task
        self.assertEqual(task.status, Task.STATUS_QUEUED)
        self.assertEqual(ProjectRun.objects.get(pk=first.json()['id']).instruction_snapshot['next_agent'], 'planning')
        self.assertEqual(Task.objects.filter(run_id=first.json()['id']).count(), 1)
        status = client.get(reverse('project_api:run_detail', args=[self.project.pk, first.json()['id']]))
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()['status'], ProjectRun.STATUS_QUEUED)

    def test_run_rejects_reused_key_with_another_message_and_non_owned_context(self):
        client = self._client_for(self.owner)
        other_conversation = Conversation.objects.create(project=self.project, owner=self.owner, title='Another run')
        first_conversation = Conversation.objects.create(project=self.project, owner=self.owner, title='First run')
        first_message = Message.objects.create(conversation=first_conversation, role=Message.ROLE_USER, content='first')
        second_message = Message.objects.create(conversation=other_conversation, role=Message.ROLE_USER, content='second')
        url = reverse('project_api:run_collection', args=[self.project.pk])
        key = '2436f1d3-30d8-4a6b-a287-3da3b56260a5'
        first_body = {'conversation_id': first_message.conversation_id, 'source_message_id': first_message.pk}
        client.post(url, data=json.dumps(first_body), content_type='application/json', HTTP_IDEMPOTENCY_KEY=key)
        reused = client.post(
            url,
            data=json.dumps({'conversation_id': other_conversation.pk, 'source_message_id': second_message.pk}),
            content_type='application/json',
            HTTP_IDEMPOTENCY_KEY=key,
        )
        invalid_key = client.post(url, data=json.dumps(first_body), content_type='application/json', HTTP_IDEMPOTENCY_KEY='not-a-uuid')
        stranger = self._client_for(self.other).post(url, data=json.dumps(first_body), content_type='application/json', HTTP_IDEMPOTENCY_KEY='f60da380-6c4f-4cde-af73-c316ea81413a')
        assistant_message = Message.objects.create(conversation=other_conversation, role=Message.ROLE_ASSISTANT, content='prototype response')
        assistant_source = client.post(
            url,
            data=json.dumps({'conversation_id': other_conversation.pk, 'source_message_id': assistant_message.pk}),
            content_type='application/json',
            HTTP_IDEMPOTENCY_KEY='3d22ed37-cfec-4d51-b52a-ce9a4cb5f8e4',
        )

        self.assertEqual(reused.status_code, 409)
        self.assertEqual(reused.json()['error']['code'], 'IDEMPOTENCY_KEY_REUSED')
        self.assertEqual(invalid_key.status_code, 422)
        self.assertEqual(stranger.status_code, 404)
        self.assertEqual(assistant_source.status_code, 404)
