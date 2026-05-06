"""
Relatorio de saude do pipeline de ingestao.

Usage:
    python manage.py ingestion_health
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.scraping.models import ScrapedOpportunity, ScrapingSource, ScrapingJob


class Command(BaseCommand):
    help = 'Relatorio de saude do pipeline de ingestao'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Numero de dias para analise (default: 7)',
        )

    def handle(self, *args, **options):
        days = options['days']
        now = timezone.now()
        cutoff = now - timedelta(days=days)

        self.stdout.write(
            f"Saude da Ingestao - consultpro.cv (ultimos {days} dias)"
        )
        self.stdout.write("=" * 60)

        # Fontes ativas
        active_sources = ScrapingSource.objects.filter(status='active').count()
        paused_sources = ScrapingSource.objects.filter(status='paused').count()
        error_sources = ScrapingSource.objects.filter(status='error').count()
        self.stdout.write(f"Fontes ativas: {active_sources}")
        self.stdout.write(f"Fontes pausadas: {paused_sources}")
        if error_sources:
            self.stdout.write(self.style.ERROR(f"Fontes com erro: {error_sources}"))

        # Processamento no periodo
        raw_processed = ScrapedOpportunity.objects.filter(scraped_at__gte=cutoff).count()
        ingested = ScrapedOpportunity.objects.filter(
            scraped_at__gte=cutoff,
            status__in=['new', 'imported']
        ).count()
        rejected = ScrapedOpportunity.objects.filter(
            scraped_at__gte=cutoff,
            status='rejected'
        ).count()
        expired = ScrapedOpportunity.objects.filter(
            scraped_at__gte=cutoff,
            status='expired'
        ).count()
        cv_eligible = ScrapedOpportunity.objects.filter(
            scraped_at__gte=cutoff,
            cv_eligible=True,
            status='new',
        ).count()

        self.stdout.write(f"Oportunidades processadas: {raw_processed}")
        self.stdout.write(f"Ativas/Importadas: {ingested}")
        self.stdout.write(f"Elegiveis para Cabo Verde (novas): {cv_eligible}")
        self.stdout.write(f"Rejeitadas: {rejected}")
        self.stdout.write(f"Expiradas: {expired}")

        # Taxa de sucesso
        if raw_processed > 0:
            success_rate = (ingested / raw_processed) * 100
            self.stdout.write(f"Taxa de ingestao: {success_rate:.1f}%")

        # Jobs recentes
        recent_jobs = ScrapingJob.objects.filter(created_at__gte=cutoff)
        if recent_jobs.exists():
            self.stdout.write(f"\nJobs executados: {recent_jobs.count()}")
            failed_jobs = recent_jobs.filter(status='failed')
            if failed_jobs.exists():
                self.stdout.write(self.style.WARNING(
                    f"Jobs falhados: {failed_jobs.count()}"
                ))
                for job in failed_jobs[:3]:
                    self.stdout.write(f"   - {job.source.name}: {job.error_log[:100]}")

        # Fontes sem atualizacao recente
        stale_threshold = now - timedelta(days=days)
        stale_sources = ScrapingSource.objects.filter(
            status='active',
            last_scraped_at__lt=stale_threshold,
        )
        if stale_sources.exists():
            self.stdout.write(self.style.WARNING(
                f"\nFontes ativas sem atualizacao (> {days} dias):"
            ))
            for src in stale_sources:
                last = src.last_scraped_at.strftime('%Y-%m-%d %H:%M') if src.last_scraped_at else 'Nunca'
                self.stdout.write(f"   - {src.name} (ultima: {last})")

        # Qualidade media
        avg_quality = ScrapedOpportunity.objects.filter(
            scraped_at__gte=cutoff
        ).values_list('data_quality_score', flat=True)
        avg_quality_list = list(avg_quality)
        if avg_quality_list:
            avg_q = sum(avg_quality_list) / len(avg_quality_list)
            self.stdout.write(f"\nQualidade media dos dados: {avg_q:.2f}/1.00")

        self.stdout.write("Checkup concluido.")
