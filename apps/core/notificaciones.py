"""
Servicio de Notificaciones — BienestarMind
- Email (Django SMTP)
- SMS via Twilio
- WhatsApp via Twilio Sandbox
"""
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _twilio_client():
    """Retorna cliente Twilio si las credenciales están configuradas."""
    sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    if not sid or not token:
        logger.warning('Twilio no configurado. Revisa TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN en .env')
        return None
    try:
        from twilio.rest import Client
        return Client(sid, token)
    except ImportError:
        logger.error('twilio no instalado. Ejecuta: pip install twilio')
        return None


# ── EMAIL ──────────────────────────────────────────────────────────────────

def enviar_email(destinatario_email, asunto, template, contexto):
    """Envía email HTML desde una plantilla."""
    try:
        html_message = render_to_string(f'emails/{template}.html', contexto)
        plain_message = strip_tags(html_message)
        send_mail(
            subject=asunto,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinatario_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Email enviado a {destinatario_email}: {asunto}')
        return True
    except Exception as e:
        logger.error(f'Error enviando email a {destinatario_email}: {e}')
        return False


def email_confirmacion_asesoria(asesoria):
    contexto = {
        'usuario': asesoria.usuario_recibe,
        'asesor': asesoria.usuario_asesor,
        'fecha': asesoria.fecha,
        'hora': asesoria.hora,
        'motivo': asesoria.motivo_asesoria,
        'titulo': 'Confirmación de Asesoría',
    }
    ok = enviar_email(
        asesoria.usuario_recibe.correo,
        '✅ Asesoría confirmada — BienestarMind SENA',
        'confirmacion_asesoria',
        contexto,
    )
    if ok:
        asesoria.notificacion_enviada = True
        asesoria.save(update_fields=['notificacion_enviada'])
    return ok


def email_confirmacion_reserva_espacio(reserva):
    contexto = {
        'usuario': reserva.usuario,
        'espacio': reserva.espacio,
        'fecha': reserva.fecha_reserva,
        'hora': reserva.hora_inicio,
        'duracion': reserva.duracion,
        'motivo': reserva.motivo_reserva,
        'titulo': 'Confirmación de Reserva de Espacio',
    }
    ok = enviar_email(
        reserva.usuario.correo,
        '✅ Reserva de espacio confirmada — BienestarMind SENA',
        'confirmacion_reserva_espacio',
        contexto,
    )
    if ok:
        reserva.notificacion_enviada = True
        reserva.save(update_fields=['notificacion_enviada'])
    return ok


def email_confirmacion_reserva_elemento(reserva):
    contexto = {
        'usuario': reserva.usuario,
        'elemento': reserva.elemento,
        'fecha': reserva.fecha_reserva,
        'descripcion': reserva.descripcion_reserva,
        'titulo': 'Confirmación de Reserva de Elemento',
    }
    ok = enviar_email(
        reserva.usuario.correo,
        '✅ Reserva de elemento confirmada — BienestarMind SENA',
        'confirmacion_reserva_elemento',
        contexto,
    )
    if ok:
        reserva.notificacion_enviada = True
        reserva.save(update_fields=['notificacion_enviada'])
    return ok


# ── SMS ────────────────────────────────────────────────────────────────────

def enviar_sms(telefono, mensaje):
    """Envía SMS via Twilio."""
    client = _twilio_client()
    if not client:
        logger.info(f'[MODO TEST] SMS a {telefono}: {mensaje}')
        return False
    try:
        numero = telefono.strip()
        if not numero.startswith('+'):
            numero = f'+57{numero}'
        message = client.messages.create(
            body=mensaje,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=numero,
        )
        logger.info(f'SMS enviado a {numero}: SID={message.sid}')
        return True
    except Exception as e:
        logger.error(f'Error SMS a {telefono}: {e}')
        return False


def sms_confirmacion_asesoria(asesoria):
    if not asesoria.usuario_recibe.telefono:
        return False
    msg = (
        f'BienestarMind SENA\n'
        f'Tu asesoría ha sido confirmada.\n'
        f'Fecha: {asesoria.fecha.strftime("%d/%m/%Y")}\n'
        f'Asesor: {asesoria.usuario_asesor.nombre_completo}\n'
        f'Motivo: {asesoria.motivo_asesoria[:80]}'
    )
    return enviar_sms(asesoria.usuario_recibe.telefono, msg)


def sms_confirmacion_reserva_espacio(reserva):
    if not reserva.usuario.telefono:
        return False
    msg = (
        f'BienestarMind SENA\n'
        f'Reserva de espacio confirmada.\n'
        f'Espacio: {reserva.espacio.nombre_del_espacio}\n'
        f'Fecha: {reserva.fecha_reserva.strftime("%d/%m/%Y")}\n'
        f'Duración: {reserva.duracion} min'
    )
    return enviar_sms(reserva.usuario.telefono, msg)


def sms_confirmacion_reserva_elemento(reserva):
    if not reserva.usuario.telefono:
        return False
    msg = (
        f'BienestarMind SENA\n'
        f'Reserva de elemento aprobada.\n'
        f'Elemento: {reserva.elemento.nombre_elemento}\n'
        f'Fecha: {reserva.fecha_reserva.strftime("%d/%m/%Y")}'
    )
    return enviar_sms(reserva.usuario.telefono, msg)


# ── WHATSAPP ───────────────────────────────────────────────────────────────

def enviar_whatsapp(telefono, mensaje):
    """Envía WhatsApp via Twilio Sandbox."""
    client = _twilio_client()
    if not client:
        logger.info(f'[MODO TEST] WhatsApp a {telefono}: {mensaje}')
        return False
    try:
        numero = telefono.strip()
        if not numero.startswith('+'):
            numero = f'+57{numero}'
        message = client.messages.create(
            body=mensaje,
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            to=f'whatsapp:{numero}',
        )
        logger.info(f'WhatsApp enviado a {numero}: SID={message.sid}')
        return True
    except Exception as e:
        logger.error(f'Error WhatsApp a {telefono}: {e}')
        return False


def whatsapp_confirmacion(usuario, titulo, detalle):
    """Notificación WhatsApp genérica."""
    if not usuario.telefono:
        return False
    msg = (
        f'*BienestarMind SENA* 🟢\n'
        f'*{titulo}*\n\n'
        f'{detalle}\n\n'
        f'_Bienestar al Aprendiz · SENA_'
    )
    return enviar_whatsapp(usuario.telefono, msg)


def notificar_asesoria_completo(asesoria):
    """Envía email + SMS + WhatsApp para una asesoría."""
    email_confirmacion_asesoria(asesoria)
    sms_confirmacion_asesoria(asesoria)
    whatsapp_confirmacion(
        asesoria.usuario_recibe,
        'Asesoría Confirmada',
        f'📅 Fecha: {asesoria.fecha.strftime("%d/%m/%Y")}\n'
        f'👨‍🏫 Asesor: {asesoria.usuario_asesor.nombre_completo}\n'
        f'📝 Motivo: {asesoria.motivo_asesoria[:100]}'
    )


def notificar_reserva_espacio_completo(reserva):
    """Envía email + SMS + WhatsApp para reserva de espacio."""
    email_confirmacion_reserva_espacio(reserva)
    sms_confirmacion_reserva_espacio(reserva)
    whatsapp_confirmacion(
        reserva.usuario,
        'Reserva de Espacio Confirmada',
        f'🏫 Espacio: {reserva.espacio.nombre_del_espacio}\n'
        f'📅 Fecha: {reserva.fecha_reserva.strftime("%d/%m/%Y")}\n'
        f'⏱ Duración: {reserva.duracion} min\n'
        f'📝 Motivo: {reserva.motivo_reserva[:100]}'
    )


def notificar_reserva_elemento_completo(reserva):
    """Envía email + SMS + WhatsApp para reserva de elemento."""
    email_confirmacion_reserva_elemento(reserva)
    sms_confirmacion_reserva_elemento(reserva)
    whatsapp_confirmacion(
        reserva.usuario,
        'Reserva de Elemento Aprobada',
        f'📦 Elemento: {reserva.elemento.nombre_elemento}\n'
        f'📅 Fecha: {reserva.fecha_reserva.strftime("%d/%m/%Y")}\n'
        f'📝 {reserva.descripcion_reserva[:100]}'
    )
