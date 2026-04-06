"""
Vistas de Reportes — BienestarMind
Centro unificado de generación de reportes PDF y Excel
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse

from apps.asesorias.models import Asesoria
from apps.elementos.models import ReservaEspacio, ReservaElemento
from apps.usuarios.models import Usuario
from django.views.decorators.cache import never_cache
from apps.reportes.generadores import (
    generar_pdf_asesorias, generar_pdf_reservas_espacios,
    generar_pdf_reservas_elementos, generar_pdf_usuarios,
    generar_excel_asesorias, generar_excel_reservas_espacios,
    generar_excel_reservas_elementos, generar_excel_usuarios,
)


@never_cache
@login_required
def index(request):
    user = request.user

    # APRENDIZ solo ve sus propios totales
    if user.es_aprendiz:
        contexto = {
            'total_asesorias': Asesoria.objects.filter(usuario_recibe=user).count(),
            'total_res_espacios': ReservaEspacio.objects.filter(usuario=user).count(),
            'total_res_elementos': ReservaElemento.objects.filter(usuario=user).count(),
            'total_usuarios': None,  # no aplica para aprendiz
            'es_aprendiz': True,
        }
    else:
        contexto = {
            'total_asesorias': Asesoria.objects.count(),
            'total_res_espacios': ReservaEspacio.objects.count(),
            'total_res_elementos': ReservaElemento.objects.count(),
            'total_usuarios': Usuario.objects.count(),
            'es_aprendiz': False,
        }

    return render(request, 'reportes/index.html', contexto)


def _filtrar_asesorias(request):
    user = request.user

    # APRENDIZ solo ve sus asesorías
    if user.es_aprendiz:
        qs = Asesoria.objects.filter(
            usuario_recibe=user
        ).select_related('usuario_asesor', 'usuario_recibe', 'ficha')
    else:
        qs = Asesoria.objects.select_related(
            'usuario_asesor', 'usuario_recibe', 'ficha'
        ).all()

    fd = request.GET.get('fecha_desde')
    fh = request.GET.get('fecha_hasta')
    estado = request.GET.get('estado')
    if fd: qs = qs.filter(fecha__gte=fd)
    if fh: qs = qs.filter(fecha__lte=fh)
    if estado: qs = qs.filter(estado=estado)
    return qs


@never_cache
@login_required
def reporte_asesorias_pdf(request):
    qs = _filtrar_asesorias(request)
    buf = generar_pdf_asesorias(qs)
    resp = HttpResponse(buf.read(), content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename="asesorias_bienestarmind.pdf"'
    return resp


@never_cache
@login_required
def reporte_asesorias_excel(request):
    qs = _filtrar_asesorias(request)
    buf = generar_excel_asesorias(qs)
    resp = HttpResponse(buf.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename="asesorias_bienestarmind.xlsx"'
    return resp


@never_cache
@login_required
def reporte_reservas_espacios_pdf(request):
    user = request.user
    if user.es_aprendiz:
        qs = ReservaEspacio.objects.filter(
            usuario=user
        ).select_related('espacio', 'espacio__sede', 'usuario', 'ficha')
    else:
        qs = ReservaEspacio.objects.select_related(
            'espacio', 'espacio__sede', 'usuario', 'ficha'
        ).all()
    buf = generar_pdf_reservas_espacios(qs)
    resp = HttpResponse(buf.read(), content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename="reservas_espacios.pdf"'
    return resp


@never_cache
@login_required
def reporte_reservas_espacios_excel(request):
    user = request.user
    if user.es_aprendiz:
        qs = ReservaEspacio.objects.filter(
            usuario=user
        ).select_related('espacio', 'espacio__sede', 'usuario', 'ficha')
    else:
        qs = ReservaEspacio.objects.select_related(
            'espacio', 'espacio__sede', 'usuario', 'ficha'
        ).all()
    buf = generar_excel_reservas_espacios(qs)
    resp = HttpResponse(buf.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename="reservas_espacios.xlsx"'
    return resp


# ── RESERVAS ELEMENTOS ─────────────────────────────────────────────────────

@never_cache
@login_required
def reporte_reservas_elementos_pdf(request):
    user = request.user
    if user.es_aprendiz:
        qs = ReservaElemento.objects.filter(
            usuario=user
        ).select_related('elemento', 'elemento__categoria', 'usuario', 'ficha')
    else:
        qs = ReservaElemento.objects.select_related(
            'elemento', 'elemento__categoria', 'usuario', 'ficha'
        ).all()
    buf = generar_pdf_reservas_elementos(qs)
    resp = HttpResponse(buf.read(), content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename="reservas_elementos.pdf"'
    return resp


@never_cache
@login_required
def reporte_reservas_elementos_excel(request):
    user = request.user
    if user.es_aprendiz:
        qs = ReservaElemento.objects.filter(
            usuario=user
        ).select_related('elemento', 'elemento__categoria', 'usuario', 'ficha')
    else:
        qs = ReservaElemento.objects.select_related(
            'elemento', 'elemento__categoria', 'usuario', 'ficha'
        ).all()
    buf = generar_excel_reservas_elementos(qs)
    resp = HttpResponse(buf.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename="reservas_elementos.xlsx"'
    return resp


# ── USUARIOS ───────────────────────────────────────────────────────────────

@never_cache
@login_required
def reporte_usuarios_pdf(request):
    # Solo STAFF puede ver reporte de usuarios
    if request.user.es_aprendiz:
        messages.error(request, 'No tienes permisos para ver este reporte.')
        return redirect('reportes:index')
    qs = Usuario.objects.prefetch_related('roles').all()
    buf = generar_pdf_usuarios(qs)
    resp = HttpResponse(buf.read(), content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename="usuarios_bienestarmind.pdf"'
    return resp


@never_cache
@login_required
def reporte_usuarios_excel(request):
    # Solo STAFF puede ver reporte de usuarios
    if request.user.es_aprendiz:
        messages.error(request, 'No tienes permisos para ver este reporte.')
        return redirect('reportes:index')
    qs = Usuario.objects.prefetch_related('roles').all()
    buf = generar_excel_usuarios(qs)
    resp = HttpResponse(buf.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename="usuarios_bienestarmind.xlsx"'
    return resp