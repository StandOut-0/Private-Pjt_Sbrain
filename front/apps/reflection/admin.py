from django.contrib import admin

from apps.reflection.models import QualityCriterion, ReflectionReport


@admin.register(QualityCriterion)
class QualityCriterionAdmin(admin.ModelAdmin):
    list_display = ('key', 'label', 'weight', 'is_active', 'sort_order', 'updated_at')
    search_fields = ('key', 'label')
    readonly_fields = ('key', 'label', 'description', 'weight', 'is_active', 'sort_order', 'updated_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ReflectionReport)
class ReflectionReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'artifact', 'total_score', 'is_mock', 'created_at')
    readonly_fields = ('artifact', 'run', 'criteria_snapshot', 'score_details', 'total_score', 'summary', 'improvements', 'is_mock', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
