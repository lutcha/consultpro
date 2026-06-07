from django.db import models
from apps.users.models import User
from apps.opportunities.models import Opportunity


class Curriculum(models.Model):
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
        ('doc', 'DOC'),
    ]
    STATUS_CHOICES = [
        ('uploaded', 'Carregado'),
        ('processing', 'A processar'),
        ('analyzed', 'Analisado'),
        ('error', 'Erro'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='curricula')
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='curricula',
    )
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='curricula/%Y/%m/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    analysis_score = models.PositiveIntegerField(null=True, blank=True)
    
    # AI Extracted data (JSON for flexibility)
    extracted_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name_plural = 'Curricula'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email} - {self.file_name}"


class CVTemplate(models.Model):
    ORG_CHOICES = [
        ('world_bank', 'World Bank'),
        ('un', 'United Nations'),
        ('eu', 'European Union'),
        ('afdb', 'African Development Bank'),
        ('usaid', 'USAID'),
        ('giz', 'GIZ'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    organization = models.CharField(max_length=20, choices=ORG_CHOICES)
    organization_name = models.CharField(max_length=200)
    description = models.TextField()
    required_sections = models.JSONField(default=list)  # [{"id": "sec-1", "name": "...", "required": true}]
    format_rules = models.JSONField(default=list)
    max_length_pages = models.PositiveIntegerField(null=True, blank=True)
    file_template = models.FileField(upload_to='cv_templates/', null=True, blank=True)
    example_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['organization', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_organization_display()})"


class TemplateMatch(models.Model):
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='template_matches')
    template = models.ForeignKey(CVTemplate, on_delete=models.CASCADE)
    match_score = models.PositiveIntegerField()  # 0-100
    missing_sections = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    adapted_content = models.JSONField(default=dict, blank=True)
    generated_file = models.FileField(upload_to='curriculum/generated/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['curriculum', 'template']
        ordering = ['-match_score']

    def __str__(self):
        return f"{self.curriculum.file_name} -> {self.template.name} ({self.match_score}%)"


class CVSuggestion(models.Model):
    TYPE_CHOICES = [
        ('missing_section', 'Secao em Falta'),
        ('format', 'Formato'),
        ('content', 'Conteudo'),
        ('keyword', 'Palavra-chave'),
        ('length', 'Extensao'),
    ]
    PRIORITY_CHOICES = [
        ('high', 'Alta'),
        ('medium', 'Media'),
        ('low', 'Baixa'),
    ]

    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='suggestions')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    message = models.TextField()
    context = models.CharField(max_length=50, blank=True)  # world_bank, un, general
    auto_fixable = models.BooleanField(default=False)
    fixed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"{self.curriculum.file_name} - {self.get_type_display()} ({self.priority})"


class CVOpportunityMatch(models.Model):
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE, related_name='opportunity_matches')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
    overall_score = models.PositiveIntegerField()
    skills_match_score = models.PositiveIntegerField()
    experience_match_score = models.PositiveIntegerField()
    education_match_score = models.PositiveIntegerField()
    language_match_score = models.PositiveIntegerField()
    matched_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    relevant_experiences = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['curriculum', 'opportunity']
        ordering = ['-overall_score']

    def __str__(self):
        return f"{self.curriculum.file_name} <-> {self.opportunity.title} ({self.overall_score}%)"
