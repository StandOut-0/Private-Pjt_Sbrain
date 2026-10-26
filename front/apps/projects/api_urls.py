from django.urls import path

from apps.execution import api as execution_api
from apps.artifacts import api as artifact_api
from apps.reflection import api as reflection_api
from apps.projects import api_views

app_name = 'project_api'

urlpatterns = [
    path('projects/', api_views.project_collection, name='project_collection'),
    path('projects/<int:project_id>/', api_views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/conversations/', api_views.conversation_collection, name='conversation_collection'),
    path('projects/<int:project_id>/conversations/<int:conversation_id>/messages/', api_views.conversation_messages, name='conversation_messages'),
    path('projects/<int:project_id>/runs/', execution_api.create_run, name='run_collection'),
    path('projects/<int:project_id>/runs/<int:run_id>/', execution_api.run_detail, name='run_detail'),
    path('projects/<int:project_id>/runs/<int:run_id>/retry/', execution_api.retry_run, name='run_retry'),
    path('projects/<int:project_id>/runs/<int:run_id>/cancel/', execution_api.cancel_run, name='run_cancel'),
    path('projects/<int:project_id>/runs/<int:run_id>/regenerate/', execution_api.regenerate_run, name='run_regenerate'),
    path('projects/<int:project_id>/events/', execution_api.project_events, name='project_events'),
    path('projects/<int:project_id>/artifacts/', artifact_api.artifact_collection, name='artifact_collection'),
    path('projects/<int:project_id>/artifacts/<int:artifact_id>/', artifact_api.artifact_detail, name='artifact_detail'),
    path('projects/<int:project_id>/artifacts/<int:artifact_id>/download/', artifact_api.artifact_download, name='artifact_download'),
    path('projects/<int:project_id>/artifacts/<int:artifact_id>/reflection/', reflection_api.artifact_reflection, name='artifact_reflection'),
]
