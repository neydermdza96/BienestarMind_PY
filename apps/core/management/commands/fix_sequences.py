# Primero crea las carpetas si no existen:
# apps/core/management/__init__.py
# apps/core/management/commands/__init__.py
# apps/core/management/commands/fix_sequences.py

from django.core.management.base import BaseCommand
from django.db import connection, models
from django.apps import apps

class Command(BaseCommand):
    help = 'Sincroniza las secuencias de PostgreSQL para todas las tablas'

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            for model in apps.get_models():
                # Solo modelos con AutoField como PK
                if isinstance(model._meta.pk, (models.AutoField, models.BigAutoField)):
                    table = model._meta.db_table
                    pk = model._meta.pk.column
                    try:
                        cursor.execute(f"""
                            SELECT setval(
                                pg_get_serial_sequence('{table}', '{pk}'),
                                COALESCE((SELECT MAX({pk}) FROM {table}), 0) + 1,
                                false
                            );
                        """)
                        self.stdout.write(self.style.SUCCESS(f'✅ {table} sincronizada'))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'⚠️  {table}: {e}'))