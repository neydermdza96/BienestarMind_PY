"""
Modelo de Asesoría — BienestarMind
"""
from django.db import models
from django.conf import settings


class Asesoria(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('REALIZADA', 'Realizada'),
        ('CANCELADA', 'Cancelada'),
    ]

    motivo_asesoria = models.TextField()
    fecha = models.DateField()
    hora = models.TimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    observaciones = models.TextField(blank=True)
    usuario_recibe = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='asesorias_recibidas',
    )
    usuario_asesor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='asesorias_dadas',
    )
    ficha = models.ForeignKey(
        'core.Ficha',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='asesorias',
    )
    notificacion_enviada = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'asesoria'
        verbose_name = 'Asesoría'
        verbose_name_plural = 'Asesorías'
        ordering = ['-fecha', '-created_at']

    def __str__(self):
        return f'Asesoría #{self.pk} — {self.usuario_recibe} — {self.fecha}'
