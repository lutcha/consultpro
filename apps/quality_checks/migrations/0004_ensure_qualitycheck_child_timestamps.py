from django.db import migrations


def ensure_timestamp_columns(apps, schema_editor):
    checks = [
        ('QCCheckCategory', ('created_at',)),
        ('QCItem', ('created_at',)),
        ('QCSuggestion', ('created_at',)),
    ]

    for model_name, field_names in checks:
        model = apps.get_model('quality_checks', model_name)
        table_name = model._meta.db_table
        existing_columns = {
            column.name
            for column in schema_editor.connection.introspection.get_table_description(
                schema_editor.connection.cursor(),
                table_name,
            )
        }
        for field_name in field_names:
            field = model._meta.get_field(field_name)
            if field.column not in existing_columns:
                schema_editor.add_field(model, field)


class Migration(migrations.Migration):

    dependencies = [
        ('quality_checks', '0003_ensure_qualitycheck_updated_at'),
    ]

    operations = [
        migrations.RunPython(ensure_timestamp_columns, migrations.RunPython.noop),
    ]
