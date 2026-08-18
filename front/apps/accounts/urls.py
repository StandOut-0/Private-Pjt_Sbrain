from django.urls import path

from apps.accounts import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login, name='login'),
    path('login/demo/', views.demo_login, name='demo_login'),
    path('login/face/', views.face_auth, name='face_auth'),
    path('logout/', views.logout, name='logout'),
]
