from django.urls import path

from apps.comingsoon import views

app_name = 'comingsoon'

urlpatterns = [
    path('', views.index, name='index'),
    path('blocked/', views.blocked, name='blocked'),
    path('manage/', views.manage, name='manage'),
    path('manage/new/', views.editor, name='editor_new'),
    path('manage/<slug:slug>/edit/', views.editor, name='editor'),
    path('manage/<slug:slug>/delete/', views.delete, name='delete'),
    path('<slug:slug>/', views.detail, name='detail'),
]
