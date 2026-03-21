"""
Context processors — BienestarMind
Variables disponibles en todos los templates automáticamente.
"""
from apps.usuarios.models import Notificacion


def sena_context(request):
    """
    Inyecta variables globales del SENA en todos los templates.
    También agrega el conteo de notificaciones no leídas para la campanita.
    """
    ctx = {
        'SENA_VERDE':   '#3d9b35',
        'SENA_NARANJA': '#f47920',
    }
    # Agregar conteo de notificaciones no leídas si el usuario está logueado
    if request.user.is_authenticated:
        ctx['notif_count'] = Notificacion.objects.filter(
            usuario=request.user, leida=False
        ).count()
    else:
        ctx['notif_count'] = 0
    return ctx
