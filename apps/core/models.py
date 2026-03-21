"""
Modelos core: Sede, Espacio, Programa, Ficha
"""
from django.db import models


class Sede(models.Model):
    nombre_sede = models.CharField(max_length=100)
    telefono_sede = models.CharField(max_length=20, blank=True)
    direccion_sede = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sede'
        verbose_name = 'Sede'
        verbose_name_plural = 'Sedes'

    def __str__(self):
        return self.nombre_sede


class Espacio(models.Model):
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='espacios')
    nombre_del_espacio = models.CharField(max_length=100)
    capacidad = models.PositiveIntegerField(default=10)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'espacios'
        verbose_name = 'Espacio'
        verbose_name_plural = 'Espacios'

    def __str__(self):
        return f'{self.nombre_del_espacio} — {self.sede}'


class Programa(models.Model):
    nombre_programa = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'programas'
        verbose_name = 'Programa'
        verbose_name_plural = 'Programas'

    def __str__(self):
        return self.nombre_programa


class Ficha(models.Model):
    JORNADA_CHOICES = [
        ('DIURNA', 'Diurna'),
        ('MANANA', 'Mañana'),
        ('TARDE', 'Tarde'),
        ('NOCTURNA', 'Nocturna'),
        ('MIXTA', 'Mixta'),
    ]

    id_ficha = models.IntegerField(primary_key=True)
    descripcion = models.CharField(max_length=200)
    jornada_ficha = models.CharField(max_length=20, choices=JORNADA_CHOICES)
    programa = models.ForeignKey(Programa, on_delete=models.CASCADE, related_name='fichas')
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ficha'
        verbose_name = 'Ficha'
        verbose_name_plural = 'Fichas'

    def __str__(self):
        return f'{self.id_ficha} — {self.descripcion}'


class UsuarioFicha(models.Model):
    from apps.usuarios.models import Usuario
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE, related_name='fichas_usuario')
    ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE, related_name='usuarios_ficha')
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usuario_ficha'
        unique_together = ('usuario', 'ficha')

    def __str__(self):
        return f'{self.usuario} / Ficha {self.ficha.id_ficha}'
