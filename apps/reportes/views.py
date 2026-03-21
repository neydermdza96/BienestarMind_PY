"""
Vistas de Reportes — BienestarMind
Centro unificado de generación de reportes PDF y Excel
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from apps.asesorias.models import Asesoria
from apps.elementos.models import ReservaEspacio, ReservaElemento
from apps.usuarios.models import Usuario
from apps.reportes.generadores import (
    generar_pdf_asesorias, generar_pdf_reservas_espacios,
    generar_pdf_reservas_elementos, generar_pdf_usuarios,
    generar_excel_asesorias, generar_excel_reservas_espacios, generar_excel_usuarios,
)


@login_required
def index(request):
    contexto = {
        'total_asesorias': Asesoria.objects.count(),
        'total_res_espacios': ReservaEspacio.objects.count(),
        'total_res_elementos': ReservaElemento.objects.count(),
        'total_usuarios': Usuario.objects.count(),
    }
    return render(request, 'reportes/index.html', contexto)


def _filtrar_asesorias(request):
    qs = Asesoria.objects.select_related('usuario_asesor', 'usuario_recibe', 'ficha').all()
    fd = request.GET.get('fecha_desde')
    fh = request.GET.get('fecha_hasta')
    estado = request.GET.get('estado')
    if fd: qs = qs.filter(fecha__gte=fd)
    if fh: qs = qs.filter(fecha__lte=fh)
    if estado: qs = qs.filter(estado=estado)
    return qs


@login_required
def reporte_asesorias_pdf(request):
    qs = _filtrar_asesorias(request)
    buf = generar_pdf_asesorias(qs)
    resp = HttpResponse(buf.read(), content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename="asesorias_bienestarmind.pdf"'
    return resp


@login_required
def reporte_asesorias_excel(request):
    qs = _filtrar_asesorias(request)
    buf = generar_excel_asesorias(qs)
    resp = HttpResponse(buf.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename="asesorias_bienestarmind.xlsx"'
    return resp


@login_required
def reporte_reservas_espacios_pdf(request):
    qs = ReservaEspacio.objects.select_related('espacio', 'espacio__sede', 'usuario', 'ficha').all()
    buf = generar_pdf_reservas_espacios(qs)
    resp = HttpResponse(buf.read(), content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename="reservas_espacios.pdf"'
    return resp


@login_required
def reporte_reservas_espacios_excel(request):
    qs = ReservaEspacio.objects.select_related('espacio', 'espacio__sede', 'usuario', 'ficha').all()
    buf = generar_excel_reservas_espacios(qs)
    resp = HttpResponse(buf.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename="reservas_espacios.xlsx"'
    return resp


@login_required
def reporte_usuarios_pdf(request):
    qs = Usuario.objects.prefetch_related('roles').all()
    buf = generar_pdf_usuarios(qs)
    resp = HttpResponse(buf.read(), content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename="usuarios_bienestarmind.pdf"'
    return resp


@login_required
def reporte_usuarios_excel(request):
    qs = Usuario.objects.prefetch_related('roles').all()
    buf = generar_excel_usuarios(qs)
    resp = HttpResponse(buf.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename="usuarios_bienestarmind.xlsx"'
    return resp
