"""
Modelos: CategoriaElemento, Elemento (con inventario/stock),
         ReservaElemento, ReservaEspacio, MovimientoInventario
"""
from django.db import models
from django.conf import settings


class CategoriaElemento(models.Model):
    descripcion = models.CharField(max_length=100)
    created_at  = models.DateTimeField(auto_now_add=True)
    update_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categoria_elementos'
        verbose_name = 'Categoría de Elemento'
        verbose_name_plural = 'Categorías de Elementos'

    def __str__(self):
        return self.descripcion


class Elemento(models.Model):
    ESTADO_CHOICES = [
        ('DISPONIBLE',    'Disponible'),
        ('EN_USO',        'En Uso'),
        ('MANTENIMIENTO', 'En Mantenimiento'),
        ('BAJA',          'Dado de Baja'),
        ('AGOTADO',       'Sin Stock'),
    ]

    categoria       = models.ForeignKey(CategoriaElemento, on_delete=models.CASCADE, related_name='elementos')
    nombre_elemento = models.CharField(max_length=150)
    descripcion     = models.TextField(blank=True)
    estado_elemento = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='DISPONIBLE')
    codigo          = models.CharField(max_length=50, blank=True, unique=True, null=True)
    # ── Inventario / Stock ─────────────────────────────────────────
    stock_total     = models.PositiveIntegerField(default=1, help_text='Cantidad total de este elemento')
    stock_disponible= models.PositiveIntegerField(default=1, help_text='Cantidad disponible para préstamo')
    stock_minimo    = models.PositiveIntegerField(default=1, help_text='Alerta cuando el stock baja de este valor')
    ubicacion       = models.CharField(max_length=100, blank=True, help_text='Ej: Sala Bienestar, Armario 2')
    # ──────────────────────────────────────────────────────────────
    created_at      = models.DateTimeField(auto_now_add=True)
    update_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elementos'
        verbose_name = 'Elemento'
        verbose_name_plural = 'Elementos'

    def __str__(self):
        return self.nombre_elemento

    @property
    def disponible(self):
        return self.stock_disponible > 0 and self.estado_elemento == 'DISPONIBLE'

    @property
    def alerta_stock(self):
        return self.stock_disponible <= self.stock_minimo

    @property
    def porcentaje_disponible(self):
        if self.stock_total == 0:
            return 0
        return round((self.stock_disponible / self.stock_total) * 100)

    def actualizar_estado(self):
        """Actualiza el estado automáticamente según el stock."""
        if self.estado_elemento in ('MANTENIMIENTO', 'BAJA'):
            return
        if self.stock_disponible == 0:
            self.estado_elemento = 'AGOTADO'
        elif self.stock_disponible < self.stock_total:
            self.estado_elemento = 'EN_USO'
        else:
            self.estado_elemento = 'DISPONIBLE'
        self.save(update_fields=['estado_elemento'])


class MovimientoInventario(models.Model):
    """
    Registro de todos los movimientos de inventario:
    entradas, salidas, devoluciones, ajustes.
    """
    TIPO_CHOICES = [
        ('ENTRADA',     'Entrada'),
        ('SALIDA',      'Salida / Préstamo'),
        ('DEVOLUCION',  'Devolución'),
        ('AJUSTE',      'Ajuste de inventario'),
        ('BAJA',        'Baja definitiva'),
    ]

    elemento    = models.ForeignKey(Elemento, on_delete=models.CASCADE, related_name='movimientos')
    tipo        = models.CharField(max_length=20, choices=TIPO_CHOICES)
    cantidad    = models.PositiveIntegerField(default=1)
    descripcion = models.TextField(blank=True)
    stock_antes = models.PositiveIntegerField()
    stock_despues = models.PositiveIntegerField()
    usuario     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='movimientos_inventario')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movimiento_inventario'
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_tipo_display()} — {self.elemento} — {self.created_at.date()}'


class ReservaElemento(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE',  'Pendiente'),
        ('APROBADA',   'Aprobada'),
        ('RECHAZADA',  'Rechazada'),
        ('DEVUELTO',   'Devuelto'),
        ('VENCIDO',    'Vencido'),
    ]

    fecha_reserva       = models.DateField()
    fecha_devolucion    = models.DateField(null=True, blank=True, help_text='Fecha prevista de devolución')
    descripcion_reserva = models.TextField()
    estado              = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    ficha               = models.ForeignKey('core.Ficha', on_delete=models.SET_NULL, null=True, blank=True)
    usuario             = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                            related_name='reservas_elementos')
    elemento            = models.ForeignKey(Elemento, on_delete=models.CASCADE, related_name='reservas')
    cantidad            = models.PositiveIntegerField(default=1)
    notificacion_enviada= models.BooleanField(default=False)
    created_at          = models.DateTimeField(auto_now_add=True)
    update_at           = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reservaelementos'
        verbose_name = 'Reserva de Elemento'
        verbose_name_plural = 'Reservas de Elementos'
        ordering = ['-fecha_reserva']

    def __str__(self):
        return f'Reserva {self.elemento} — {self.usuario} — {self.fecha_reserva}'


class ReservaEspacio(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE',  'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('RECHAZADA',  'Rechazada'),
        ('CANCELADA',  'Cancelada'),
    ]

    fecha_reserva   = models.DateField()
    hora_inicio     = models.TimeField(null=True, blank=True)
    motivo_reserva  = models.TextField()
    estado          = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    duracion        = models.PositiveIntegerField(help_text='Duración en minutos', default=60)
    ficha           = models.ForeignKey('core.Ficha', on_delete=models.SET_NULL, null=True, blank=True)
    usuario         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                        related_name='reservas_espacios')
    espacio         = models.ForeignKey('core.Espacio', on_delete=models.CASCADE, related_name='reservas')
    notificacion_enviada = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)
    update_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reservaespacios'
        verbose_name = 'Reserva de Espacio'
        verbose_name_plural = 'Reservas de Espacios'
        ordering = ['-fecha_reserva']

    def __str__(self):
        return f'Reserva {self.espacio} — {self.usuario} — {self.fecha_reserva}'

    def hay_conflicto(self):
        return ReservaEspacio.objects.filter(
            espacio=self.espacio, fecha_reserva=self.fecha_reserva, estado='CONFIRMADA',
        ).exclude(pk=self.pk).exists()
