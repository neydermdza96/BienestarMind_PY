from django.core.management.base import BaseCommand
from apps.usuarios.models import Usuario, Rol, UsuarioRol

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if Usuario.objects.filter(documento='admin001').exists():
            self.stdout.write('Ya existe el administrador')
            return
        user = Usuario(
            documento='admin001',
            nombres='ADMINISTRADOR',
            apellidos='PRINCIPAL',
            correo='bienestarmind2026@gmail.com',
            genero='NO_ESPECIFICA',
            fecha_de_nacimiento='1990-01-01',
            is_staff=True,
            is_superuser=True,
        )
        user.set_password('Admin2026*')
        user.save()
        rol = Rol.objects.get(descripcion='ADMINISTRADOR')
        UsuarioRol.objects.create(usuario=user, rol=rol)
        self.stdout.write('✅ Administrador creado')
