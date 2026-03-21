"""Admin de BienestarMind"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.usuarios.models import Usuario, Rol, UsuarioRol, Permiso, RolPermiso
from apps.core.models import Sede, Espacio, Programa, Ficha, UsuarioFicha
from apps.asesorias.models import Asesoria
from apps.elementos.models import CategoriaElemento, Elemento, ReservaElemento, ReservaEspacio

admin.site.site_header = "BienestarMind SENA — Administración"
admin.site.site_title = "BienestarMind Admin"
admin.site.index_title = "Panel de Administración"


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = ['documento', 'nombre_completo', 'correo', 'is_active', 'edad']
    list_filter = ['is_active', 'genero', 'roles']
    search_fields = ['nombres', 'apellidos', 'documento', 'correo']
    ordering = ['apellidos']
    fieldsets = (
        (None, {'fields': ('documento', 'password')}),
        ('Información Personal', {'fields': ('nombres', 'apellidos', 'correo', 'genero', 'telefono', 'fecha_de_nacimiento', 'foto')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('documento', 'nombres', 'apellidos', 'correo', 'fecha_de_nacimiento', 'password1', 'password2')}),
    )


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'created_at']


@admin.register(UsuarioRol)
class UsuarioRolAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'rol', 'created_at']
    list_filter = ['rol']


@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ['nombre_sede', 'telefono_sede', 'direccion_sede']


@admin.register(Espacio)
class EspacioAdmin(admin.ModelAdmin):
    list_display = ['nombre_del_espacio', 'sede', 'capacidad', 'activo']
    list_filter = ['sede', 'activo']


@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ['nombre_programa']
    search_fields = ['nombre_programa']


@admin.register(Ficha)
class FichaAdmin(admin.ModelAdmin):
    list_display = ['id_ficha', 'descripcion', 'jornada_ficha', 'programa']
    list_filter = ['jornada_ficha', 'programa']
    search_fields = ['id_ficha', 'descripcion']


@admin.register(Asesoria)
class AsesoriaAdmin(admin.ModelAdmin):
    list_display = ['pk', 'fecha', 'usuario_asesor', 'usuario_recibe', 'estado', 'notificacion_enviada']
    list_filter = ['estado', 'notificacion_enviada']
    search_fields = ['motivo_asesoria', 'usuario_recibe__nombres']
    date_hierarchy = 'fecha'


@admin.register(Elemento)
class ElementoAdmin(admin.ModelAdmin):
    list_display = ['nombre_elemento', 'categoria', 'estado_elemento', 'codigo']
    list_filter = ['estado_elemento', 'categoria']
    search_fields = ['nombre_elemento', 'codigo']


@admin.register(CategoriaElemento)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['descripcion']


@admin.register(ReservaEspacio)
class ReservaEspacioAdmin(admin.ModelAdmin):
    list_display = ['pk', 'fecha_reserva', 'espacio', 'usuario', 'estado', 'notificacion_enviada']
    list_filter = ['estado', 'espacio__sede']
    date_hierarchy = 'fecha_reserva'


@admin.register(ReservaElemento)
class ReservaElementoAdmin(admin.ModelAdmin):
    list_display = ['pk', 'fecha_reserva', 'elemento', 'usuario', 'estado']
    list_filter = ['estado']
