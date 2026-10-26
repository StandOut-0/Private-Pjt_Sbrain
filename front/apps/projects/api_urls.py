from django.urls import path

from apps.execution import api as execution_api
from apps.projects import api_views

app_name = 'project_api'

urlpatterns = [
    path('projects/', api_views.project_collection, name='project_collection'),
    path('projects/<int:project_id>/', api_views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/conversations/', api_views.conversation_collection, name='conversation_collection'),
    path('projects/<int:project_id>/conversations/<int:conversation_id>/messages/', api_views.conversation_messages, name='conversation_messages'),
    path('projects/<int:project_id>/runs/', execution_api.create_run, name='run_collection'),
    path('projects/<int:project_id>/runs/<int:run_id>/', execution_api.run_detail, name='run_detail'),
]
