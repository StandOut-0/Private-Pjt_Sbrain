from django.urls import path

from apps.dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('notifications/', views.notifications, name='notifications'),
    path('user-guide/', views.user_guide, name='user_guide'),
    path('faq/', views.faq, name='faq'),
]
