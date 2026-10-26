from django.contrib import admin

from apps.reflection.models import QualityCriterion


@admin.register(QualityCriterion)
class QualityCriterionAdmin(admin.ModelAdmin):
    list_display = ('key', 'label', 'weight', 'is_active', 'sort_order', 'updated_at')
    search_fields = ('key', 'label')
