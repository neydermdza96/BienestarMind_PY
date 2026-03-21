"""
Modelo PQRS — BienestarMind
Peticiones, Quejas, Reclamos, Sugerencias y Felicitaciones
"""
from django.db import models
from django.conf import settings


class PQRS(models.Model):
    TIPO_CHOICES = [
        ('PETICION',       'Petición'),
        ('QUEJA',          'Queja'),
        ('RECLAMO',        'Reclamo'),
        ('SUGERENCIA',     'Sugerencia'),
        ('FELICITACION',   'Felicitación'),
    ]
    ESTADO_CHOICES = [
        ('PENDIENTE',   'Pendiente'),
        ('EN_REVISION', 'En Revisión'),
        ('RESPONDIDA',  'Respondida'),
        ('CERRADA',     'Cerrada'),
    ]
    PRIORIDAD_CHOICES = [
        ('BAJA',   'Baja'),
        ('MEDIA',  'Media'),
        ('ALTA',   'Alta'),
        ('URGENTE','Urgente'),
    ]

    tipo        = models.CharField(max_length=20, choices=TIPO_CHOICES)
    asunto      = models.CharField(max_length=200)
    descripcion = models.TextField()
    estado      = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    prioridad   = models.CharField(max_length=10, choices=PRIORIDAD_CHOICES, default='MEDIA')
    # Usuario que la envía (puede ser anónimo si no está logueado)
    usuario     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='pqrs_enviadas'
    )
    nombre_anonimo = models.CharField(max_length=100, blank=True, help_text='Si no está registrado')
    correo_contacto= models.EmailField(blank=True, help_text='Para enviar respuesta')
    # Respuesta del administrador
    respuesta   = models.TextField(blank=True)
    respondida_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='pqrs_respondidas'
    )
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    # Número de radicado único
    radicado    = models.CharField(max_length=20, unique=True, editable=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    update_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pqrs'
        verbose_name = 'PQRS'
        verbose_name_plural = 'PQRS'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.radicado} — {self.get_tipo_display()} — {self.asunto[:50]}'

    def save(self, *args, **kwargs):
        if not self.radicado:
            import datetime, random
            hoy = datetime.date.today()
            self.radicado = f"BM-{hoy.year}{hoy.month:02d}{hoy.day:02d}-{random.randint(1000,9999)}"
        super().save(*args, **kwargs)

    @property
    def nombre_remitente(self):
        if self.usuario:
            return self.usuario.nombre_completo
        return self.nombre_anonimo or 'Anónimo'
