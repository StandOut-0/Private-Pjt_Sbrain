from django.db import models


class Artifact(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='artifacts')
    task = models.ForeignKey('execution.Task', on_delete=models.PROTECT, related_name='artifacts')
    agent_execution = models.ForeignKey('execution.AgentExecution', on_delete=models.PROTECT, related_name='artifacts')
    artifact_type = models.CharField(max_length=40)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    logical_key = models.CharField(max_length=100)
    version = models.CharField(max_length=32)
    content = models.TextField()
    mime_type = models.CharField(max_length=100, default='application/json; charset=utf-8')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sb_artifact'
        ordering = ['-created_at', '-id']
        constraints = [models.UniqueConstraint(fields=['project', 'logical_key', 'version'], name='sb_artifact_proj_key_ver_uniq')]

