from django.core.exceptions import ValidationError
from django.db import models


class QualityCriterion(models.Model):
    key = models.SlugField(max_length=50, unique=True)
    label = models.CharField(max_length=120)
    description = models.CharField(max_length=300, blank=True, default='')
    weight = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sb_quality_criterion'
        ordering = ['sort_order', 'id']

    def clean(self):
        if self.weight > 100:
            raise ValidationError({'weight': '가중치는 100 이하이어야 합니다.'})


class ReflectionReport(models.Model):
    artifact = models.OneToOneField('artifacts.Artifact', on_delete=models.CASCADE, related_name='reflection_report')
    run = models.ForeignKey('execution.ProjectRun', on_delete=models.CASCADE, related_name='reflection_reports')
    criteria_snapshot = models.JSONField()
    score_details = models.JSONField()
    total_score = models.PositiveSmallIntegerField()
    summary = models.TextField()
    improvements = models.JSONField(default=list)
    is_mock = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sb_reflection_report'
        ordering = ['-created_at', '-id']

