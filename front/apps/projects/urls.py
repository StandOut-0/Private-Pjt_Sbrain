from django.urls import path

from apps.projects import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_detail, name='detail'),

    path('list/', views.project_list, name='list'),
    path('create/', views.project_create, name='create'),
    path('<int:project_id>/', views.project_detail, name='detail'),
    path('<int:project_id>/chat/', views.chat_reply, name='chat_reply'),
]
