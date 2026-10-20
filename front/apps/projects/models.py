from django.db import models


class Project(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_ARCHIVED = 'archived'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, '진행 중'),
        (STATUS_COMPLETED, '완료'),
        (STATUS_ARCHIVED, '보관'),
    ]

    id = models.BigAutoField(primary_key=True, db_column='project_id')
    owner = models.ForeignKey(
        'accounts.UserAccount',
        db_column='user_id',
        on_delete=models.PROTECT,
        related_name='owned_projects',
    )
    project_name = models.CharField(max_length=80)
    description = models.CharField(max_length=500, blank=True, default='')
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sb_project'
        ordering = ['-updated_at', '-id']
        indexes = [models.Index(fields=['owner', 'updated_at'], name='sb_proj_owner_upd_idx')]

    def __str__(self):
        return self.project_name
