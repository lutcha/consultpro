from django.core.management.base import BaseCommand, CommandError

from apps.knowledge.services import SUPPORTED_INDEX_SOURCE_CHOICES, run_knowledge_reindex
from apps.knowledge.tasks import index_knowledge_assets_task


class Command(BaseCommand):
    help = 'Reindex Knowledge assets from proposals, projects, curriculum, or all sources.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            choices=SUPPORTED_INDEX_SOURCE_CHOICES,
            default='all',
            help='Source to reindex.',
        )
        parser.add_argument(
            '--async',
            action='store_true',
            dest='async_mode',
            help='Queue the reindex through Celery instead of running inline.',
        )

    def handle(self, *args, **options):
        source = options['source']
        if options['async_mode']:
            task = index_knowledge_assets_task.delay(source=source)
            self.stdout.write(self.style.SUCCESS(f'Queued Knowledge reindex source={source} task_id={task.id}'))
            return

        try:
            run = run_knowledge_reindex(source=source)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        style = self.style.SUCCESS if run.status == 'completed' else self.style.WARNING
        self.stdout.write(
            style(
                f'Knowledge reindex run={run.id} source={run.source} status={run.status} '
                f'indexed={run.indexed_count} errors={run.error_count}'
            )
        )
        for source_name, stats in run.stats.get('sources', {}).items():
            self.stdout.write(f'- {source_name}: indexed={stats.get("indexed", 0)}')
        for error in run.errors:
            self.stdout.write(self.style.ERROR(f'- {error.get("source")}: {error.get("error")}'))
