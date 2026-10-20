from django.urls import path

from apps.projects import api_views

app_name = 'project_api'

urlpatterns = [
    path('projects/<int:project_id>/', api_views.project_detail, name='project_detail'),
]
