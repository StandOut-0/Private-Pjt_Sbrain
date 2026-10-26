from django.db import models


class KnowledgeDocument(models.Model):
    SCOPE_GLOBAL = 'global'
    SCOPE_PROJECT = 'project'
    SCOPE_CHOICES = [
        (SCOPE_GLOBAL, '전체 공통'),
        (SCOPE_PROJECT, '프로젝트별'),
    ]

    title = models.CharField(max_length=200)
    original_name = models.CharField(max_length=255)
    scope = models.CharField(max_length=16, choices=SCOPE_CHOICES)
    project = models.ForeignKey(
        'projects.Project', null=True, blank=True, on_delete=models.CASCADE,
        related_name='knowledge_documents',
    )
    content = models.TextField()
    uploaded_by = models.ForeignKey(
        'accounts.UserAccount', on_delete=models.PROTECT,
        related_name='uploaded_knowledge_documents',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sb_knowledge_document'
        ordering = ['-updated_at', '-id']

    def __str__(self):
        return self.title
