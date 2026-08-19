from django.urls import path

from apps.management import views

app_name = 'management'

urlpatterns = [
    path('tasks/', views.task_list, name='tasks'),
    path('agents/', views.agent_list, name='agents'),
    path('agents/<str:key>/', views.agent_detail, name='agent_detail'),
    path('results/', views.results, name='results'),
]
