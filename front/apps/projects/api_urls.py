from django.urls import path

from apps.projects import api_views

app_name = 'project_api'

urlpatterns = [
    path('projects/', api_views.project_collection, name='project_collection'),
    path('projects/<int:project_id>/', api_views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/conversations/', api_views.conversation_collection, name='conversation_collection'),
    path('projects/<int:project_id>/conversations/<int:conversation_id>/messages/', api_views.conversation_messages, name='conversation_messages'),
]
