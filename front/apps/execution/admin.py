from django.contrib import admin

from apps.execution.models import Agent, AgentExecution, ExecutionEvent, ProjectRun, Task


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('key', 'name', 'group', 'is_active')
    list_filter = ('group', 'is_active')
    search_fields = ('key', 'name')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'project', 'status', 'created_at', 'started_at', 'finished_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'project__project_name')


@admin.register(ProjectRun)
class ProjectRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'requested_by', 'status', 'retry_count', 'created_at', 'finished_at')
    list_filter = ('status', 'created_at')
    search_fields = ('project__project_name', 'idempotency_key')
    readonly_fields = ('idempotency_key', 'instruction_snapshot')


@admin.register(AgentExecution)
class AgentExecutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'agent', 'task', 'status', 'provider_name', 'model_name', 'input_tokens', 'output_tokens', 'estimated_cost_usd', 'is_retryable')
    list_filter = ('status', 'agent', 'provider_name', 'is_retryable')
    search_fields = ('task__title', 'error_code', 'error_message')
    readonly_fields = ('input', 'output', 'error_message')


@admin.register(ExecutionEvent)
class ExecutionEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'event_type', 'from_status', 'to_status', 'created_at')
    list_filter = ('event_type', 'to_status', 'created_at')
    search_fields = ('project__project_name', 'message')
    readonly_fields = ('metadata',)
