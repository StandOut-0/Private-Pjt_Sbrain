from django.urls import path

from apps.reflection import api

app_name = 'reflection_api'

urlpatterns = [
    path('', api.criteria, name='criteria'),
    path('replace/', api.replace_criteria, name='criteria_replace'),
]
