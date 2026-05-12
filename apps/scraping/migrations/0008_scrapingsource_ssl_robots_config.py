from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraping', '0007_add_grants_civil_society_sources'),
    ]

    operations = [
        migrations.AddField(
            model_name='scrapingsource',
            name='verify_ssl',
            field=models.BooleanField(
                default=True,
                help_text='Verify SSL certificates when fetching',
            ),
        ),
        migrations.AddField(
            model_name='scrapingsource',
            name='respect_robots_txt',
            field=models.BooleanField(
                default=True,
                help_text='Honour robots.txt directives',
            ),
        ),
    ]
