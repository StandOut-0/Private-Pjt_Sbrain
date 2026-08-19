from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('apps.dashboard.urls')),
    path('', include('apps.accounts.urls')),
    path('projects/', include('apps.projects.urls')),
    path('manage/', include('apps.management.urls')),
    path('coming-soon/', include('apps.comingsoon.urls')),
]
