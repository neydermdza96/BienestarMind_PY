from django.db import migrations, models


def normalizar_estados_reservas(apps, schema_editor):
    ReservaEspacio = apps.get_model('elementos', 'ReservaEspacio')
    ReservaElemento = apps.get_model('elementos', 'ReservaElemento')

    ReservaEspacio.objects.filter(estado='CONFIRMADA').update(estado='APROBADA')
    ReservaEspacio.objects.filter(estado='RECHAZADA').update(estado='NO_DISPONIBLE')

    ReservaElemento.objects.filter(estado='RECHAZADA').update(estado='NO_DISPONIBLE')
    ReservaElemento.objects.filter(estado='DEVUELTO').update(estado='CANCELADA')
    ReservaElemento.objects.filter(estado='VENCIDO').update(estado='NO_DISPONIBLE')


def reversa_normalizar_estados_reservas(apps, schema_editor):
    ReservaEspacio = apps.get_model('elementos', 'ReservaEspacio')
    ReservaElemento = apps.get_model('elementos', 'ReservaElemento')

    ReservaEspacio.objects.filter(estado='APROBADA').update(estado='CONFIRMADA')
    ReservaEspacio.objects.filter(estado='NO_DISPONIBLE').update(estado='RECHAZADA')

    ReservaElemento.objects.filter(estado='NO_DISPONIBLE').update(estado='RECHAZADA')
    ReservaElemento.objects.filter(estado='CANCELADA').update(estado='DEVUELTO')


class Migration(migrations.Migration):

    dependencies = [
        ('elementos', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservaelemento',
            name='estado',
            field=models.CharField(
                choices=[
                    ('PENDIENTE', 'Pendiente'),
                    ('APROBADA', 'Aprobada'),
                    ('NO_DISPONIBLE', 'No disponible'),
                    ('CANCELADA', 'Cancelada'),
                ],
                default='PENDIENTE',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='reservaespacio',
            name='estado',
            field=models.CharField(
                choices=[
                    ('PENDIENTE', 'Pendiente'),
                    ('APROBADA', 'Aprobada'),
                    ('NO_DISPONIBLE', 'No disponible'),
                    ('CANCELADA', 'Cancelada'),
                ],
                default='PENDIENTE',
                max_length=20,
            ),
        ),
        migrations.RunPython(
            normalizar_estados_reservas,
            reversa_normalizar_estados_reservas
        ),
    ]