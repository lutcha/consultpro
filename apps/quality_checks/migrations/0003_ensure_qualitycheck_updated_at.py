from django.db import migrations


def ensure_qualitycheck_updated_at(apps, schema_editor):
    QualityCheck = apps.get_model('quality_checks', 'QualityCheck')
    table_name = QualityCheck._meta.db_table
    existing_columns = {
        column.name
        for column in schema_editor.connection.introspection.get_table_description(
            schema_editor.connection.cursor(),
            table_name,
        )
    }

    field = QualityCheck._meta.get_field('updated_at')
    if field.column not in existing_columns:
        schema_editor.add_field(QualityCheck, field)


class Migration(migrations.Migration):

    dependencies = [
        ('quality_checks', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(ensure_qualitycheck_updated_at, migrations.RunPython.noop),
    ]
