from django.db import migrations


DEFAULT_TENANT_SLUG = 'consultpro-internal'


def create_default_tenant_and_backfill(apps, schema_editor):
    Tenant = apps.get_model('tenants', 'Tenant')
    TenantProfile = apps.get_model('tenants', 'TenantProfile')
    TenantStrategy = apps.get_model('tenants', 'TenantStrategy')
    TenantIntelligenceProfile = apps.get_model('tenants', 'TenantIntelligenceProfile')

    tenant, _created = Tenant.objects.get_or_create(
        slug=DEFAULT_TENANT_SLUG,
        defaults={
            'name': 'ConsultPro Internal',
            'status': 'active',
            'plan': 'beta',
            'organization_type': 'consulting_firm',
            'size': 'small',
            'maturity_level': 'growing',
            'primary_country': 'cv',
            'default_language': 'pt',
        },
    )
    TenantProfile.objects.get_or_create(tenant=tenant)
    TenantStrategy.objects.get_or_create(tenant=tenant)
    TenantIntelligenceProfile.objects.get_or_create(tenant=tenant)

    for app_label, model_name in [
        ('opportunities', 'Opportunity'),
        ('opportunities', 'FirmProfile'),
        ('opportunities', 'SavedFilter'),
        ('proposals', 'Proposal'),
        ('scraping', 'ScrapingSource'),
        ('scraping', 'ScrapedOpportunity'),
        ('scraping', 'ScrapingJob'),
        ('scraping', 'ScrapingAlert'),
        ('curriculum', 'Curriculum'),
        ('knowledge', 'KnowledgeAsset'),
        ('partners', 'PartnerProfile'),
        ('projects', 'Project'),
        ('notifications', 'Notification'),
        ('notifications', 'ActivityLog'),
        ('ai_services', 'AIConfiguration'),
        ('analytics', 'PredictiveMetric'),
        ('analytics', 'MarketSignal'),
    ]:
        model = apps.get_model(app_label, model_name)
        model.objects.filter(tenant__isnull=True).update(tenant=tenant)

    UserInvitation = apps.get_model('users', 'UserInvitation')
    UserInvitation.objects.filter(tenant__isnull=True).update(tenant=tenant)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('tenants', '0001_initial'),
        ('ai_services', '0002_aiconfiguration_tenant'),
        ('analytics', '0002_marketsignal_tenant_predictivemetric_tenant'),
        ('curriculum', '0005_curriculum_tenant'),
        ('knowledge', '0003_knowledgeasset_tenant'),
        ('notifications', '0004_activitylog_tenant_notification_tenant'),
        ('opportunities', '0010_firmprofile_tenant_opportunity_tenant_and_more'),
        ('partners', '0002_partnerprofile_tenant'),
        ('projects', '0007_project_tenant'),
        ('proposals', '0014_proposal_tenant'),
        ('scraping', '0013_scrapedopportunity_tenant_scrapingalert_tenant_and_more'),
        ('users', '0003_userinvitation_tenant_userinvitation_tenant_role'),
    ]

    operations = [
        migrations.RunPython(create_default_tenant_and_backfill, noop_reverse),
    ]
