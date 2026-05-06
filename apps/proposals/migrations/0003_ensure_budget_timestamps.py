from django.db import migrations


def ensure_budget_timestamps(apps, schema_editor):
    Budget = apps.get_model('proposals', 'Budget')
    table_name = Budget._meta.db_table
    existing_columns = {
        column.name
        for column in schema_editor.connection.introspection.get_table_description(
            schema_editor.connection.cursor(),
            table_name,
        )
    }

    for field_name in ('created_at', 'updated_at'):
        field = Budget._meta.get_field(field_name)
        if field.column not in existing_columns:
            schema_editor.add_field(Budget, field)


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(ensure_budget_timestamps, migrations.RunPython.noop),
    ]
