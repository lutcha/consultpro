from django.db import models
from apps.users.models import User


class ScrapingSource(models.Model):
    TYPE_CHOICES = [
        ('portal', 'Portal'),
        ('rss', 'RSS Feed'),
        ('api', 'API'),
        ('job_board', 'Job Board'),
    ]
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('paused', 'Pausado'),
        ('error', 'Erro'),
        ('disabled', 'Desativado'),
    ]
    FREQUENCY_CHOICES = [
        ('hourly', 'Por Hora'),
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
    ]

    name = models.CharField(max_length=200)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='scraping_sources',
    )
    organization = models.CharField(max_length=200)
    url = models.URLField()
    logo = models.URLField(blank=True)
    source_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='portal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Scraping configuration
    scrape_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    last_scraped_at = models.DateTimeField(null=True, blank=True)
    next_scrape_at = models.DateTimeField(null=True, blank=True)
    
    # Filters stored as JSON
    filters = models.JSONField(default=dict, blank=True)  # {sectors: [], countries: [], keywords: []}
    
    # Scraping logic
    scraper_class = models.CharField(max_length=100, default='BaseScraper')
    scraper_config = models.JSONField(default=dict, blank=True)  # {selector: "...", parser: "..."}

    # Network / compliance settings
    verify_ssl = models.BooleanField(default=True, help_text='Verify SSL certificates when fetching')
    respect_robots_txt = models.BooleanField(default=True, help_text='Honour robots.txt directives')
    
    # Statistics
    new_opportunities_count = models.PositiveIntegerField(default=0)
    total_opportunities_count = models.PositiveIntegerField(default=0)
    success_rate = models.PositiveIntegerField(default=100)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class ScrapedOpportunity(models.Model):
    STATUS_CHOICES = [
        ('new', 'Nova'),
        ('imported', 'Importada'),
        ('ignored', 'Ignorada'),
        ('expired', 'Expirada'),
        ('rejected', 'Rejeitada'),
    ]

    source = models.ForeignKey(ScrapingSource, on_delete=models.CASCADE, related_name='scraped_opportunities')
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='scraped_opportunities',
    )
    external_id = models.CharField(max_length=200, blank=True)
    external_url = models.URLField()
    
    # Opportunity data
    title = models.CharField(max_length=500)
    organization = models.CharField(max_length=200)
    client = models.CharField(max_length=200, blank=True)
    sector = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    deadline = models.DateTimeField(null=True, blank=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    published_at = models.DateTimeField(null=True, blank=True)
    deadline_alert = models.BooleanField(default=False)
    
    # AI processing
    ai_summary = models.TextField(blank=True)
    ai_extracted_requirements = models.JSONField(default=list, blank=True)

    # Deep extraction from opportunity detail pages / linked ToR PDFs
    deep_content_text = models.TextField(blank=True)
    deep_content_url = models.URLField(max_length=1000, blank=True)
    deep_content_status = models.CharField(max_length=20, blank=True)
    deep_content_extracted_at = models.DateTimeField(null=True, blank=True)
    
    # === Pipeline de Ingestão Defensiva ===
    # Proveniência: dados brutos preservados (imutáveis)
    raw_payload = models.JSONField(default=dict, blank=True)
    raw_content_hash = models.CharField(max_length=64, db_index=True, blank=True)
    
    # Validação de prazos
    deadline_validation = models.JSONField(default=dict, blank=True)
    deadline_timezone = models.CharField(max_length=50, default="Atlantic/Cape_Verde")
    
    # Elegibilidade para Cabo Verde
    cv_eligible = models.BooleanField(default=False, db_index=True)
    eligibility_data = models.JSONField(default=dict, blank=True)
    
    # Metadados técnicos
    data_quality_score = models.DecimalField(max_digits=3, decimal_places=2, default=1.00)
    transformation_flags = models.JSONField(default=dict, blank=True)
    language = models.CharField(max_length=10, blank=True)
    sector_tags = models.JSONField(default=list, blank=True)
    geographic_scope = models.JSONField(default=dict, blank=True)
    ingestion_batch_id = models.CharField(max_length=40, blank=True, db_index=True)
    
    # Relation to internal opportunity (if imported)
    imported_opportunity = models.OneToOneField(
        'opportunities.Opportunity',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scraped_source'
    )
    imported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    imported_at = models.DateTimeField(null=True, blank=True)
    
    scraped_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-scraped_at']
        unique_together = ['source', 'external_id']
        indexes = [
            models.Index(fields=['status', 'scraped_at']),
            models.Index(fields=['cv_eligible', 'deadline']),
            models.Index(fields=['ingestion_batch_id']),
        ]

    def __str__(self):
        return f"{self.title} ({self.source.name})"


class ScrapingJob(models.Model):
    STATUS_CHOICES = [
        ('running', 'A executar'),
        ('completed', 'Completo'),
        ('failed', 'Falhou'),
        ('scheduled', 'Agendado'),
    ]
    EXECUTED_BY_CHOICES = [
        ('scheduler', 'Agendador'),
        ('manual', 'Manual'),
        ('user', 'Utilizador'),
    ]

    source = models.ForeignKey(ScrapingSource, on_delete=models.CASCADE, related_name='jobs')
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='scraping_jobs',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    items_found = models.PositiveIntegerField(default=0)
    items_new = models.PositiveIntegerField(default=0)
    items_imported = models.PositiveIntegerField(default=0)
    items_rejected = models.PositiveIntegerField(default=0)
    items_duplicate = models.PositiveIntegerField(default=0)
    
    error_log = models.TextField(blank=True)
    executed_by = models.CharField(max_length=20, choices=EXECUTED_BY_CHOICES, default='scheduler')
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Pipeline stats
    batch_stats = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.source.name} - {self.get_status_display()}"


class ScrapingAlert(models.Model):
    TYPE_CHOICES = [
        ('new_opportunity', 'Nova Oportunidade'),
        ('deadline_approaching', 'Prazo Proximo'),
        ('status_change', 'Alteracao de Estado'),
        ('value_threshold', 'Valor Acima do Limite'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scraping_alerts')
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='scraping_alerts',
    )
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    scraped_opportunity = models.ForeignKey(ScrapedOpportunity, on_delete=models.CASCADE, null=True, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.user.email})"
