import time

from django.core.management.base import BaseCommand, CommandError

from apps.execution.models import ProjectRun
from apps.execution.planning import process_run


class Command(BaseCommand):
    help = 'Process queued ProjectRuns with the configured Planning provider.'

    def add_arguments(self, parser):
        parser.add_argument('--run-id', type=int)
        parser.add_argument('--once', action='store_true', help='Process at most one queued run and exit.')
        parser.add_argument('--poll-seconds', type=float, default=2.0)

    def handle(self, *args, **options):
        run_id = options['run_id']
        if run_id is not None:
            try:
                run = process_run(run_id)
            except ProjectRun.DoesNotExist as exc:
                raise CommandError(f'Run {run_id} does not exist.') from exc
            self.stdout.write(f'Run {run.pk}: {run.status}')
            return

        poll_seconds = max(0.2, options['poll_seconds'])
        while True:
            pending_id = ProjectRun.objects.filter(status=ProjectRun.STATUS_QUEUED).order_by('created_at', 'id').values_list('id', flat=True).first()
            if pending_id is None:
                if options['once']:
                    self.stdout.write('No queued runs.')
                    return
                time.sleep(poll_seconds)
                continue
            try:
                run = process_run(pending_id)
                self.stdout.write(f'Run {run.pk}: {run.status}')
            except Exception as exc:
                self.stderr.write(f'Run {pending_id} processing failed: {exc.__class__.__name__}')
            if options['once']:
                return
