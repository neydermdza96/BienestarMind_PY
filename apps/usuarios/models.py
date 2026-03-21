"""
Modelo de Usuario personalizado — BienestarMind
+ Modelo TokenRecuperacion para reset de contraseña
"""
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
import datetime
import uuid


def validar_edad_minima(fecha_nacimiento):
    hoy = datetime.date.today()
    edad = (hoy - fecha_nacimiento).days // 365
    if edad < settings.EDAD_MINIMA:
        raise ValidationError(
            f'El usuario debe tener al menos {settings.EDAD_MINIMA} años de edad. '
            f'Edad actual: {edad} años.'
        )


class Rol(models.Model):
    ROLES = [
        ('ADMINISTRADOR', 'Administrador'),
        ('INSTRUCTOR', 'Instructor'),
        ('APRENDIZ', 'Aprendiz'),
        ('COORDINADOR', 'Coordinador'),
    ]
    descripcion = models.CharField(max_length=50, choices=ROLES, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'roles'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.descripcion


class Permiso(models.Model):
    descripcion = models.CharField(max_length=100)
    created_at  = models.DateTimeField(auto_now_add=True)
    update_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'permisos'

    def __str__(self):
        return self.descripcion


class RolPermiso(models.Model):
    rol     = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name='permisos')
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'roles_permisos'
        unique_together = ('rol', 'permiso')


class UsuarioManager(BaseUserManager):
    def create_user(self, documento, password=None, **extra_fields):
        if not documento:
            raise ValueError('El documento es obligatorio')
        user = self.model(documento=documento, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, documento, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(documento, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    GENERO_CHOICES = [
        ('MASCULINO',    'Masculino'),
        ('FEMENINO',     'Femenino'),
        ('OTRO',         'Otro'),
        ('NO_ESPECIFICA','Prefiero no especificar'),
    ]

    nombres              = models.CharField(max_length=100)
    apellidos            = models.CharField(max_length=100)
    documento            = models.CharField(max_length=20, unique=True)
    correo               = models.EmailField(unique=True)
    genero               = models.CharField(max_length=20, choices=GENERO_CHOICES, default='NO_ESPECIFICA')
    telefono             = models.CharField(max_length=20, blank=True)
    fecha_de_nacimiento  = models.DateField(validators=[validar_edad_minima])
    foto                 = models.ImageField(upload_to='usuarios/fotos/', blank=True, null=True)
    roles                = models.ManyToManyField(Rol, through='UsuarioRol', blank=True)
    is_active            = models.BooleanField(default=True)
    is_staff             = models.BooleanField(default=False)
    created_at           = models.DateTimeField(auto_now_add=True)
    update_at            = models.DateTimeField(auto_now=True)

    USERNAME_FIELD  = 'documento'
    REQUIRED_FIELDS = ['nombres', 'apellidos', 'correo', 'fecha_de_nacimiento']

    objects = UsuarioManager()

    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.nombres} {self.apellidos} ({self.documento})'

    @property
    def nombre_completo(self):
        return f'{self.nombres} {self.apellidos}'

    @property
    def edad(self):
        hoy = datetime.date.today()
        return (hoy - self.fecha_de_nacimiento).days // 365

    @property
    def rol_principal(self):
        ur = self.usuario_roles.first()
        return ur.rol if ur else None

    def tiene_rol(self, *roles):
        return self.roles.filter(descripcion__in=roles).exists()

    @property
    def es_admin(self):
        return self.tiene_rol('ADMINISTRADOR')

    @property
    def es_coordinador(self):
        return self.tiene_rol('COORDINADOR')

    @property
    def es_instructor(self):
        return self.tiene_rol('INSTRUCTOR')

    @property
    def es_aprendiz(self):
        return self.tiene_rol('APRENDIZ')

    @property
    def es_admin_o_coordinador(self):
        return self.tiene_rol('ADMINISTRADOR', 'COORDINADOR')

    @property
    def es_staff_nivel(self):
        """INSTRUCTOR, COORDINADOR o ADMINISTRADOR"""
        return self.tiene_rol('INSTRUCTOR', 'COORDINADOR', 'ADMINISTRADOR')

    def get_initials(self):
        return f"{self.nombres[0]}{self.apellidos[0]}".upper() if self.nombres and self.apellidos else "?"


class UsuarioRol(models.Model):
    usuario    = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='usuario_roles')
    rol        = models.ForeignKey(Rol, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'usuario_roles'
        unique_together = ('usuario', 'rol')

    def __str__(self):
        return f'{self.usuario} — {self.rol}'


# ── TOKEN DE RECUPERACIÓN DE CONTRASEÑA ───────────────────────────────────
class TokenRecuperacion(models.Model):
    """
    Token único de un solo uso para recuperar contraseña.
    Expira a las 2 horas de ser generado.
    Se invalida automáticamente al usarse.
    """
    usuario    = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='tokens_recuperacion')
    token      = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    usado      = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    HORAS_VALIDEZ = 2  # El token expira en 2 horas

    class Meta:
        db_table = 'token_recuperacion'
        verbose_name = 'Token de Recuperación'
        ordering = ['-created_at']

    def __str__(self):
        return f'Token {self.usuario.documento} — {"usado" if self.usado else "activo"}'

    @property
    def expirado(self):
        from django.utils import timezone
        limite = self.created_at + datetime.timedelta(hours=self.HORAS_VALIDEZ)
        return timezone.now() > limite

    @property
    def valido(self):
        return not self.usado and not self.expirado


# ── HORARIO DE INSTRUCTORES ────────────────────────────────────────
class HorarioInstructor(models.Model):
    """
    Bloqueo de disponibilidad horaria de instructores.
    Un instructor puede marcar horas ocupadas o disponibles.
    """
    DIAS_CHOICES = [
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'),
        (3, 'Jueves'), (4, 'Viernes'), (5, 'Sábado'),
    ]
    TIPO_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('OCUPADO',    'Ocupado / Bloqueado'),
        ('ASESORIA',   'Asesoría programada'),
        ('REUNION',    'Reunión'),
        ('CAPACITACION','Capacitación'),
    ]

    instructor  = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='horarios',
        limit_choices_to={'roles__descripcion__in': ['INSTRUCTOR','COORDINADOR','ADMINISTRADOR']}
    )
    fecha       = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin    = models.TimeField()
    tipo        = models.CharField(max_length=20, choices=TIPO_CHOICES, default='DISPONIBLE')
    descripcion = models.CharField(max_length=200, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'horario_instructor'
        verbose_name = 'Horario'
        verbose_name_plural = 'Horarios'
        ordering = ['fecha', 'hora_inicio']

    def __str__(self):
        return f'{self.instructor.nombre_completo} — {self.fecha} {self.hora_inicio}-{self.hora_fin}'


# ── NOTIFICACIONES IN-APP ──────────────────────────────────────────
class Notificacion(models.Model):
    """
    Notificaciones internas dentro del sistema (in-app).
    Se muestran en el topbar como campanita.
    """
    TIPO_CHOICES = [
        ('ASESORIA',   'Asesoría'),
        ('RESERVA',    'Reserva'),
        ('INVENTARIO', 'Inventario'),
        ('PQRS',       'PQRS'),
        ('SISTEMA',    'Sistema'),
        ('HORARIO',    'Horario'),
    ]

    usuario     = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones')
    tipo        = models.CharField(max_length=20, choices=TIPO_CHOICES, default='SISTEMA')
    titulo      = models.CharField(max_length=150)
    mensaje     = models.TextField()
    url         = models.CharField(max_length=300, blank=True, help_text='URL a la que redirige al hacer clic')
    leida       = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notificacion'
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.usuario} — {self.titulo}'
