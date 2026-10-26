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

