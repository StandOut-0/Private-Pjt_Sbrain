from django.db import models


class Agent(models.Model):
    key = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=100)
    group = models.CharField(max_length=40, blank=True, default='worker')
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'sb_agent'
        ordering = ['name']

    def __str__(self):
        return self.name


class Task(models.Model):
    STATUS_QUEUED = 'queued'
    STATUS_RUNNING = 'running'
    STATUS_WAITING_FOR_USER = 'waiting_for_user'
    STATUS_SUCCEEDED = 'succeeded'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_QUEUED, '대기'),
        (STATUS_RUNNING, '진행 중'),
        (STATUS_WAITING_FOR_USER, '사용자 입력 대기'),
        (STATUS_SUCCEEDED, '완료'),
        (STATUS_FAILED, '실패'),
        (STATUS_CANCELLED, '취소'),
    ]

    id = models.BigAutoField(primary_key=True, db_column='task_id')
    run = models.OneToOneField('execution.ProjectRun', db_column='run_id', on_delete=models.CASCADE, related_name='planning_task')
    project = models.ForeignKey('projects.Project', db_column='project_id', on_delete=models.CASCADE, related_name='execution_tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    priority = models.CharField(max_length=16, default='normal')
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'sb_task'
        ordering = ['-created_at', '-id']
        indexes = [models.Index(fields=['project', 'run'], name='sb_task_proj_run_idx')]


class ProjectRun(models.Model):
    STATUS_QUEUED = 'queued'
    STATUS_RUNNING = 'running'
    STATUS_CANCEL_REQUESTED = 'cancel_requested'
    STATUS_CANCELLED = 'cancelled'
    STATUS_SUCCEEDED = 'succeeded'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_QUEUED, '대기'),
        (STATUS_RUNNING, '진행 중'),
        (STATUS_CANCEL_REQUESTED, '중단 요청'),
        (STATUS_CANCELLED, '중단'),
        (STATUS_SUCCEEDED, '성공'),
        (STATUS_FAILED, '실패'),
    ]

    id = models.BigAutoField(primary_key=True, db_column='run_id')
    project = models.ForeignKey('projects.Project', db_column='project_id', on_delete=models.CASCADE, related_name='runs')
    requested_by = models.ForeignKey('accounts.UserAccount', db_column='requested_by', on_delete=models.PROTECT, related_name='project_runs')
    conversation = models.ForeignKey('projects.Conversation', db_column='conversation_id', on_delete=models.PROTECT, related_name='runs')
    source_message = models.ForeignKey('projects.Message', db_column='source_message_id', on_delete=models.PROTECT, related_name='runs')
    previous_run = models.ForeignKey('self', db_column='previous_run_id', null=True, blank=True, on_delete=models.PROTECT, related_name='retries')
    idempotency_key = models.CharField(max_length=128)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    feedback = models.TextField(blank=True, default='')
    instruction_snapshot = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    cancel_requested_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'sb_project_run'
        ordering = ['-created_at', '-id']
        constraints = [
            models.UniqueConstraint(fields=['project', 'idempotency_key'], name='sb_run_proj_idem_uniq'),
        ]
        indexes = [models.Index(fields=['project', 'created_at'], name='sb_run_proj_created_idx')]


class AgentExecution(models.Model):
    STATUS_QUEUED = 'queued'
    STATUS_RUNNING = 'running'
    STATUS_CANCEL_REQUESTED = 'cancel_requested'
    STATUS_CANCELLED = 'cancelled'
    STATUS_SUCCEEDED = 'succeeded'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_QUEUED, '대기'),
        (STATUS_RUNNING, '진행 중'),
        (STATUS_CANCEL_REQUESTED, '중단 요청'),
        (STATUS_CANCELLED, '중단'),
        (STATUS_SUCCEEDED, '성공'),
        (STATUS_FAILED, '실패'),
    ]

    id = models.BigAutoField(primary_key=True, db_column='execution_id')
    task = models.ForeignKey(Task, db_column='task_id', on_delete=models.CASCADE, related_name='executions')
    agent = models.ForeignKey(Agent, db_column='agent_id', on_delete=models.PROTECT, related_name='executions')
    input = models.TextField(blank=True, default='')
    output = models.TextField(blank=True, default='')
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    attempt_number = models.PositiveSmallIntegerField(default=1)
    is_required = models.BooleanField(default=True)
    error_code = models.CharField(max_length=80, blank=True, default='')
    error_message = models.TextField(blank=True, default='')
    is_retryable = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'sb_agent_execution'
        ordering = ['-started_at', '-id']
        constraints = [
            models.UniqueConstraint(fields=['task', 'agent', 'attempt_number'], name='sb_exec_task_agent_attempt_uniq'),
        ]
