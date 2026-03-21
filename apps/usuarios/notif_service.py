"""
Servicio de Notificaciones In-App — BienestarMind
Crea notificaciones internas que aparecen en la campanita del topbar.
"""
from apps.usuarios.models import Notificacion


def crear_notificacion(usuario, tipo, titulo, mensaje, url=''):
    """Crea una notificación in-app para un usuario."""
    try:
        Notificacion.objects.create(
            usuario=usuario, tipo=tipo,
            titulo=titulo, mensaje=mensaje, url=url,
        )
    except Exception:
        pass


def notif_asesoria_nueva(asesoria):
    crear_notificacion(
        usuario=asesoria.usuario_recibe,
        tipo='ASESORIA',
        titulo='Nueva asesoría programada',
        mensaje=f'Tienes una asesoría el {asesoria.fecha.strftime("%d/%m/%Y")} con {asesoria.usuario_asesor.nombre_completo}',
        url='/asesorias/',
    )
    crear_notificacion(
        usuario=asesoria.usuario_asesor,
        tipo='ASESORIA',
        titulo='Asesoría asignada',
        mensaje=f'Tienes una asesoría el {asesoria.fecha.strftime("%d/%m/%Y")} con {asesoria.usuario_recibe.nombre_completo}',
        url='/asesorias/',
    )


def notif_reserva_espacio(reserva):
    crear_notificacion(
        usuario=reserva.usuario,
        tipo='RESERVA',
        titulo='Reserva de espacio confirmada',
        mensaje=f'{reserva.espacio.nombre_del_espacio} — {reserva.fecha_reserva.strftime("%d/%m/%Y")}',
        url='/reservas/espacios/',
    )


def notif_reserva_elemento(reserva):
    crear_notificacion(
        usuario=reserva.usuario,
        tipo='RESERVA',
        titulo='Solicitud de elemento aprobada',
        mensaje=f'{reserva.elemento.nombre_elemento} — {reserva.fecha_reserva.strftime("%d/%m/%Y")}',
        url='/reservas/elementos/',
    )


def notif_pqrs_respondida(pqrs):
    if pqrs.usuario:
        crear_notificacion(
            usuario=pqrs.usuario,
            tipo='PQRS',
            titulo=f'Tu PQRS {pqrs.radicado} fue respondida',
            mensaje=pqrs.respuesta[:120] + ('...' if len(pqrs.respuesta) > 120 else ''),
            url='/pqrs/mis-pqrs/',
        )


def notif_stock_bajo(elemento, usuario_admin):
    crear_notificacion(
        usuario=usuario_admin,
        tipo='INVENTARIO',
        titulo=f'Stock bajo: {elemento.nombre_elemento}',
        mensaje=f'Solo quedan {elemento.stock_disponible} unidades de {elemento.nombre_elemento}',
        url='/elementos/inventario/',
    )
