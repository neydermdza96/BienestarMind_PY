"""
Vistas Core — BienestarMind
Dashboard, Fichas, Programas, Sedes, Espacios
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms
from django.views.decorators.cache import never_cache

from apps.core.models import Sede, Espacio, Programa, Ficha, UsuarioFicha
from apps.asesorias.models import Asesoria
from apps.elementos.models import ReservaEspacio, ReservaElemento, Elemento
from apps.usuarios.models import Usuario




# ─── CONTEXT PROCESSOR ────────────────────────────────────────────────────
def sena_context(request):
    return {'SENA_VERDE': '#3d9b35', 'SENA_NARANJA': '#f47920'}


# ─── DASHBOARD ─────────────────────────────────────────────────────────────
@never_cache
@login_required
def dashboard(request):
    user = request.user

    # ── Dashboard APRENDIZ: solo sus propios datos ──────────────────────────
    if user.es_aprendiz:
        mis_asesorias = Asesoria.objects.filter(usuario_recibe=user)
        mis_reservas_espacios = ReservaEspacio.objects.filter(usuario=user)
        mis_reservas_elementos = ReservaElemento.objects.filter(usuario=user)

        return render(request, 'core/dashboard_aprendiz.html', {
            'stats': {
                'asesorias': mis_asesorias.count(),
                'asesorias_pendientes': mis_asesorias.filter(estado='PENDIENTE').count(),
                'asesorias_confirmadas': mis_asesorias.filter(estado='CONFIRMADA').count(),
                'reservas_espacios': mis_reservas_espacios.count(),
                'reservas_elementos': mis_reservas_elementos.count(),
            },
            'ultimas_asesorias': mis_asesorias.select_related(
                'usuario_asesor'
            ).order_by('-created_at')[:5],
        })

    # ── Dashboard STAFF: vista global ──────────────────────────────────────
    return render(request, 'core/dashboard.html', {
        'stats': {
            'usuarios': Usuario.objects.count(),
            'asesorias': Asesoria.objects.count(),
            'reservas_espacios': ReservaEspacio.objects.count(),
            'reservas_elementos': ReservaElemento.objects.count(),
            'fichas': Ficha.objects.count(),
            'elementos': Elemento.objects.count(),
        },
        'ultimas_asesorias': Asesoria.objects.select_related(
            'usuario_recibe', 'usuario_asesor'
        ).order_by('-created_at')[:5],
        'sedes': Sede.objects.prefetch_related('espacios').all(),
    })


# ─── FICHAS ────────────────────────────────────────────────────────────────
class FichaForm(forms.ModelForm):
    class Meta:
        model = Ficha
        fields = ['id_ficha', 'descripcion', 'jornada_ficha', 'programa']
        widgets = {
            'id_ficha': forms.NumberInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'jornada_ficha': forms.Select(attrs={'class': 'form-select'}),
            'programa': forms.Select(attrs={'class': 'form-select'}),
        }

@never_cache
@login_required
def fichas(request):
    qs = Ficha.objects.select_related('programa').all()
    q = request.GET.get('q', '')
    prog = request.GET.get('programa', '')
    if q:
        qs = qs.filter(descripcion__icontains=q) | qs.filter(id_ficha__icontains=q)
    if prog:
        qs = qs.filter(programa__id=prog)
    return render(request, 'core/fichas.html', {
        'fichas': qs,
        'programas': Programa.objects.all(),
        'q': q, 'programa': prog,
    })

@never_cache
@login_required
def crear_ficha(request):
    if not request.user.tiene_rol('ADMINISTRADOR', 'COORDINADOR'):
        messages.error(request, 'Sin permisos.'); return redirect('core:fichas')
    form = FichaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Ficha creada.')
        return redirect('core:fichas')
    return render(request, 'core/ficha_form.html', {'form': form, 'titulo': 'Nueva Ficha'})

@never_cache
@login_required
def editar_ficha(request, pk):
    if not request.user.tiene_rol('ADMINISTRADOR', 'COORDINADOR'):
        messages.error(request, 'Sin permisos.'); return redirect('core:fichas')
    ficha = get_object_or_404(Ficha, pk=pk)
    form = FichaForm(request.POST or None, instance=ficha)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Ficha actualizada.')
        return redirect('core:fichas')
    return render(request, 'core/ficha_form.html', {'form': form, 'titulo': f'Editar Ficha {ficha.id_ficha}'})

@never_cache
@login_required
def eliminar_ficha(request, pk):
    if not request.user.tiene_rol('ADMINISTRADOR'):
        messages.error(request, 'Sin permisos.'); return redirect('core:fichas')
    get_object_or_404(Ficha, pk=pk).delete()
    messages.success(request, 'Ficha eliminada.')
    return redirect('core:fichas')


# ─── PROGRAMAS ─────────────────────────────────────────────────────────────
class ProgramaForm(forms.ModelForm):
    class Meta:
        model = Programa
        fields = ['nombre_programa', 'descripcion']
        widgets = {
            'nombre_programa': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

@never_cache
@login_required
def programas(request):
    qs = Programa.objects.prefetch_related('fichas').all()
    return render(request, 'core/programas.html', {'programas': qs})

@never_cache
@login_required
def crear_programa(request):
    if not request.user.tiene_rol('ADMINISTRADOR', 'COORDINADOR'):
        messages.error(request, 'Sin permisos.'); return redirect('core:programas')
    form = ProgramaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Programa creado.')
        return redirect('core:programas')
    return render(request, 'core/programa_form.html', {'form': form, 'titulo': 'Nuevo Programa'})

@never_cache
@login_required
def editar_programa(request, pk):
    if not request.user.tiene_rol('ADMINISTRADOR', 'COORDINADOR'):
        messages.error(request, 'Sin permisos.'); return redirect('core:programas')
    prog = get_object_or_404(Programa, pk=pk)
    form = ProgramaForm(request.POST or None, instance=prog)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Programa actualizado.')
        return redirect('core:programas')
    return render(request, 'core/programa_form.html', {'form': form, 'titulo': f'Editar: {prog.nombre_programa}'})


# ─── SEDES ─────────────────────────────────────────────────────────────────
class SedeForm(forms.ModelForm):
    class Meta:
        model = Sede
        fields = ['nombre_sede', 'telefono_sede', 'direccion_sede']
        widgets = {
            'nombre_sede': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_sede': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion_sede': forms.TextInput(attrs={'class': 'form-control'}),
        }


class EspacioForm(forms.ModelForm):
    class Meta:
        model = Espacio
        fields = ['sede', 'nombre_del_espacio', 'capacidad', 'descripcion', 'activo']
        widgets = {
            'sede': forms.Select(attrs={'class': 'form-select'}),
            'nombre_del_espacio': forms.TextInput(attrs={'class': 'form-control'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

@never_cache
@login_required
def sedes(request):
    qs = Sede.objects.prefetch_related('espacios').all()
    return render(request, 'core/sedes.html', {'sedes': qs})

@never_cache
@login_required
def crear_sede(request):
    if not request.user.tiene_rol('ADMINISTRADOR'):
        messages.error(request, 'Sin permisos.'); return redirect('core:sedes')
    form = SedeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Sede creada.')
        return redirect('core:sedes')
    return render(request, 'core/sede_form.html', {'form': form, 'titulo': 'Nueva Sede'})

@never_cache
@login_required
def editar_sede(request, pk):
    if not request.user.tiene_rol('ADMINISTRADOR'):
        messages.error(request, 'Sin permisos.'); return redirect('core:sedes')
    sede = get_object_or_404(Sede, pk=pk)
    form = SedeForm(request.POST or None, instance=sede)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Sede actualizada.')
        return redirect('core:sedes')
    return render(request, 'core/sede_form.html', {'form': form, 'titulo': f'Editar: {sede.nombre_sede}'})

@never_cache
@login_required
def crear_espacio(request):
    if not request.user.tiene_rol('ADMINISTRADOR', 'COORDINADOR'):
        messages.error(request, 'Sin permisos.'); return redirect('core:sedes')
    form = EspacioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Espacio creado.')
        return redirect('core:sedes')
    return render(request, 'core/espacio_form.html', {'form': form, 'titulo': 'Nuevo Espacio'})

@never_cache
@login_required
def editar_espacio(request, pk):
    if not request.user.tiene_rol('ADMINISTRADOR', 'COORDINADOR'):
        messages.error(request, 'Sin permisos.'); return redirect('core:sedes')
    esp = get_object_or_404(Espacio, pk=pk)
    form = EspacioForm(request.POST or None, instance=esp)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Espacio actualizado.')
        return redirect('core:sedes')
    return render(request, 'core/espacio_form.html', {'form': form, 'titulo': f'Editar: {esp.nombre_del_espacio}'})

@never_cache
@login_required
def eliminar_espacio(request, pk):
    if not request.user.tiene_rol('ADMINISTRADOR'):
        messages.error(request, 'Sin permisos.'); return redirect('core:sedes')
    get_object_or_404(Espacio, pk=pk).delete()
    messages.success(request, 'Espacio eliminado.')
    return redirect('core:sedes')


# ─── LANDING PAGE PÚBLICA ──────────────────────────────────────────
from django.views.decorators.cache import cache_page


def landing(request):
    if request.user.is_authenticated:
        from django.urls import reverse
        return redirect(reverse('core:dashboard'))
    return render(request, 'core/landing.html', {
        'year': __import__('datetime').date.today().year,
    })


# ─── PANEL INSTRUCTOR ─────────────────────────────────────────────
@never_cache
@login_required
def panel_instructor(request):
    if not request.user.tiene_rol('INSTRUCTOR','ADMINISTRADOR','COORDINADOR'):
        messages.error(request, 'Acceso restringido a Instructores.')
        return redirect('core:dashboard')
    from apps.asesorias.models import Asesoria
    from apps.elementos.models import ReservaElemento, ReservaEspacio
    from apps.usuarios.models import Usuario
    return render(request, 'core/panel_instructor.html', {
        'mis_asesorias': Asesoria.objects.filter(
            usuario_asesor=request.user
        ).select_related('usuario_recibe','ficha').order_by('-fecha')[:10],
        'proximas_asesorias': Asesoria.objects.filter(
            usuario_asesor=request.user,
            fecha__gte=__import__('datetime').date.today(),
            estado__in=['PENDIENTE','CONFIRMADA'],
        ).order_by('fecha')[:5],
        'total_asesorias': Asesoria.objects.filter(usuario_asesor=request.user).count(),
        'total_aprendices': Usuario.objects.filter(roles__descripcion='APRENDIZ').count(),
        'reservas_pendientes': ReservaEspacio.objects.filter(
            usuario=request.user, estado='PENDIENTE'
        ).count(),
    })


# ─── PANEL COORDINADOR ────────────────────────────────────────────
@never_cache
@login_required
def panel_coordinador(request):
    if not request.user.tiene_rol('COORDINADOR','ADMINISTRADOR'):
        messages.error(request, 'Acceso restringido a Coordinadores.')
        return redirect('core:dashboard')
    from apps.asesorias.models import Asesoria
    from apps.elementos.models import ReservaElemento, ReservaEspacio, Elemento
    from apps.usuarios.models import Usuario
    import datetime as dt

    hoy = dt.date.today()
    elementos = Elemento.objects.select_related('categoria').all()
    alertas_stock = [e for e in elementos if e.alerta_stock and e.estado_elemento not in ('BAJA',)]

    return render(request, 'core/panel_coordinador.html', {
        # Estadísticas generales
        'total_usuarios':    Usuario.objects.filter(is_active=True).count(),
        'total_aprendices':  Usuario.objects.filter(roles__descripcion='APRENDIZ').count(),
        'total_instructores':Usuario.objects.filter(roles__descripcion='INSTRUCTOR').count(),
        # Asesorías
        'asesorias_hoy':     Asesoria.objects.filter(fecha=hoy).count(),
        'asesorias_mes':     Asesoria.objects.filter(fecha__month=hoy.month, fecha__year=hoy.year).count(),
        'asesorias_pendientes': Asesoria.objects.filter(estado='PENDIENTE').count(),
        'ultimas_asesorias': Asesoria.objects.select_related(
            'usuario_asesor','usuario_recibe'
        ).order_by('-fecha')[:8],
        # Reservas
        'reservas_espacio_hoy': ReservaEspacio.objects.filter(fecha_reserva=hoy).count(),
        'reservas_pendientes':  ReservaEspacio.objects.filter(estado='PENDIENTE').count(),
        'reservas_elementos_activas': ReservaElemento.objects.filter(estado='APROBADA').count(),
        # Inventario
        'alertas_stock':     alertas_stock,
        'total_elementos':   elementos.count(),
        'elementos_agotados':elementos.filter(estado_elemento='AGOTADO').count(),
        # Instructores con actividad
        'instructores': Usuario.objects.filter(
            roles__descripcion='INSTRUCTOR', is_active=True
        ).prefetch_related('asesorias_dadas')[:10],
    })


# ═══════════════════════════════════════════════════════════════════
# CALENDARIO VISUAL DE RESERVAS Y ASESORÍAS
# ═══════════════════════════════════════════════════════════════════
import json
from django.http import JsonResponse
@never_cache
@login_required
def calendario(request):
    """Vista del calendario visual con asesorías y reservas de espacios."""
    from apps.core.models import Espacio
    espacios = Espacio.objects.select_related('sede').all()
    return render(request, 'core/calendario.html', {
        'espacios': espacios,
    })

@never_cache
@login_required
def calendario_api(request):
    """
    API JSON para FullCalendar.
    Devuelve asesorías + reservas de espacios como eventos del calendario.
    """
    from apps.asesorias.models import Asesoria
    from apps.elementos.models import ReservaEspacio
    import datetime

    fecha_inicio = request.GET.get('start', '')
    fecha_fin    = request.GET.get('end', '')
    espacio_id   = request.GET.get('espacio', '')

    eventos = []

    # ── Asesorías ──────────────────────────────────────────────────
    qs_asesoria = Asesoria.objects.select_related('usuario_asesor', 'usuario_recibe').all()
    if fecha_inicio:
        qs_asesoria = qs_asesoria.filter(fecha__gte=fecha_inicio[:10])
    if fecha_fin:
        qs_asesoria = qs_asesoria.filter(fecha__lte=fecha_fin[:10])
    # Aprendices solo ven sus propias asesorías
    if request.user.tiene_rol('APRENDIZ') and not request.user.tiene_rol('ADMINISTRADOR','COORDINADOR','INSTRUCTOR'):
        qs_asesoria = qs_asesoria.filter(usuario_recibe=request.user)

    COLOR_ASESORIA = {
        'PENDIENTE':  '#f47920',
        'CONFIRMADA': '#3d9b35',
        'REALIZADA':  '#64748b',
        'CANCELADA':  '#a32d2d',
    }
    for a in qs_asesoria:
        hora_inicio = a.hora.strftime('%H:%M') if a.hora else '08:00'
        hora_fin    = (datetime.datetime.combine(a.fecha, a.hora) +
                       datetime.timedelta(hours=1)).strftime('%H:%M') if a.hora else '09:00'
        eventos.append({
            'id':       f'asesoria_{a.pk}',
            'title':    f'Asesoría: {a.usuario_recibe.nombre_completo}',
            'start':    f'{a.fecha}T{hora_inicio}',
            'end':      f'{a.fecha}T{hora_fin}',
            'color':    COLOR_ASESORIA.get(a.estado, '#3d9b35'),
            'extendedProps': {
                'tipo':    'asesoria',
                'asesor':  a.usuario_asesor.nombre_completo,
                'recibe':  a.usuario_recibe.nombre_completo,
                'motivo':  a.motivo_asesoria[:100],
                'estado':  a.get_estado_display(),
                'url':     f'/asesorias/{a.pk}/editar/',
            }
        })

    # ── Reservas de espacios ───────────────────────────────────────
    qs_reserva = ReservaEspacio.objects.select_related('espacio','espacio__sede','usuario').all()
    if fecha_inicio:
        qs_reserva = qs_reserva.filter(fecha_reserva__gte=fecha_inicio[:10])
    if fecha_fin:
        qs_reserva = qs_reserva.filter(fecha_reserva__lte=fecha_fin[:10])
    if espacio_id:
        qs_reserva = qs_reserva.filter(espacio__id=espacio_id)
    if request.user.tiene_rol('APRENDIZ') and not request.user.tiene_rol('ADMINISTRADOR','COORDINADOR','INSTRUCTOR'):
        qs_reserva = qs_reserva.filter(usuario=request.user)

    COLOR_RESERVA = {
        'PENDIENTE':  '#854F0B',
        'CONFIRMADA': '#185FA5',
        'RECHAZADA':  '#a32d2d',
        'CANCELADA':  '#94a3b8',
    }
    for r in qs_reserva:
        hora_inicio = r.hora_inicio.strftime('%H:%M') if r.hora_inicio else '08:00'
        if r.hora_inicio:
            hora_fin = (datetime.datetime.combine(r.fecha_reserva, r.hora_inicio) +
                       datetime.timedelta(minutes=r.duracion)).strftime('%H:%M')
        else:
            hora_fin = '09:00'
        eventos.append({
            'id':    f'reserva_{r.pk}',
            'title': f'{r.espacio.nombre_del_espacio}',
            'start': f'{r.fecha_reserva}T{hora_inicio}',
            'end':   f'{r.fecha_reserva}T{hora_fin}',
            'color': COLOR_RESERVA.get(r.estado, '#185FA5'),
            'extendedProps': {
                'tipo':    'reserva_espacio',
                'espacio': r.espacio.nombre_del_espacio,
                'sede':    r.espacio.sede.nombre_sede,
                'usuario': r.usuario.nombre_completo,
                'motivo':  r.motivo_reserva[:100],
                'estado':  r.get_estado_display(),
                'duracion':f'{r.duracion} min',
            }
        })

    # ── Horarios de instructores ───────────────────────────────────
    from apps.usuarios.models import HorarioInstructor
    qs_horario = HorarioInstructor.objects.select_related('instructor').all()
    if fecha_inicio:
        qs_horario = qs_horario.filter(fecha__gte=fecha_inicio[:10])
    if fecha_fin:
        qs_horario = qs_horario.filter(fecha__lte=fecha_fin[:10])

    COLOR_HORARIO = {
        'DISPONIBLE':   '#0F6E56',
        'OCUPADO':      '#993C1D',
        'ASESORIA':     '#3d9b35',
        'REUNION':      '#534AB7',
        'CAPACITACION': '#854F0B',
    }
    for h in qs_horario:
        eventos.append({
            'id':    f'horario_{h.pk}',
            'title': f'{h.get_tipo_display()}: {h.instructor.apellidos}',
            'start': f'{h.fecha}T{h.hora_inicio.strftime("%H:%M")}',
            'end':   f'{h.fecha}T{h.hora_fin.strftime("%H:%M")}',
            'color': COLOR_HORARIO.get(h.tipo, '#64748b'),
            'textColor': '#fff',
            'extendedProps': {
                'tipo':       'horario',
                'instructor': h.instructor.nombre_completo,
                'descripcion':h.descripcion,
            }
        })

    return JsonResponse(eventos, safe=False)


# ═══════════════════════════════════════════════════════════════════
# HORARIOS DE INSTRUCTORES
# ═══════════════════════════════════════════════════════════════════
from django import forms as dj_forms

class HorarioForm(dj_forms.Form):
    fecha       = dj_forms.DateField(
        widget=dj_forms.DateInput(attrs={'class':'form-control','type':'date'}))
    hora_inicio = dj_forms.TimeField(
        widget=dj_forms.TimeInput(attrs={'class':'form-control','type':'time'}))
    hora_fin    = dj_forms.TimeField(
        widget=dj_forms.TimeInput(attrs={'class':'form-control','type':'time'}))
    tipo        = dj_forms.ChoiceField(
        widget=dj_forms.Select(attrs={'class':'form-select'}))
    descripcion = dj_forms.CharField(
        required=False,
        widget=dj_forms.TextInput(attrs={'class':'form-control','placeholder':'Observaciones...'}))

    def __init__(self, *args, **kwargs):
        from apps.usuarios.models import HorarioInstructor
        super().__init__(*args, **kwargs)
        self.fields['tipo'].choices = HorarioInstructor.TIPO_CHOICES

    def clean(self):
        cleaned = super().clean()
        hi = cleaned.get('hora_inicio')
        hf = cleaned.get('hora_fin')
        if hi and hf and hf <= hi:
            raise dj_forms.ValidationError('La hora de fin debe ser posterior a la de inicio.')
        return cleaned

@never_cache
@login_required
def horarios(request):
    """Lista de horarios del instructor logueado (o todos si es admin)."""
    from apps.usuarios.models import HorarioInstructor, Usuario
    if request.user.tiene_rol('ADMINISTRADOR','COORDINADOR'):
        qs = HorarioInstructor.objects.select_related('instructor').all()
        instructores = Usuario.objects.filter(roles__descripcion__in=['INSTRUCTOR','COORDINADOR','ADMINISTRADOR']).distinct()
    else:
        qs = HorarioInstructor.objects.filter(instructor=request.user)
        instructores = None
    return render(request, 'core/horarios.html', {
        'horarios': qs[:60],
        'instructores': instructores,
    })

@never_cache
@login_required
def crear_horario(request):
    """Crear un bloque de horario."""
    from apps.usuarios.models import HorarioInstructor
    if not request.user.tiene_rol('INSTRUCTOR','ADMINISTRADOR','COORDINADOR'):
        messages.error(request,'Sin permisos.'); return redirect('core:horarios')
    form = HorarioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        HorarioInstructor.objects.create(
            instructor  = request.user,
            fecha       = form.cleaned_data['fecha'],
            hora_inicio = form.cleaned_data['hora_inicio'],
            hora_fin    = form.cleaned_data['hora_fin'],
            tipo        = form.cleaned_data['tipo'],
            descripcion = form.cleaned_data.get('descripcion',''),
        )
        messages.success(request, 'Bloque de horario creado.')
        return redirect('core:calendario')
    return render(request, 'core/horario_form.html', {'form': form})

@never_cache
@login_required
def eliminar_horario(request, pk):
    from apps.usuarios.models import HorarioInstructor
    h = get_object_or_404(HorarioInstructor, pk=pk)
    if h.instructor != request.user and not request.user.tiene_rol('ADMINISTRADOR'):
        messages.error(request,'Sin permisos.'); return redirect('core:horarios')
    h.delete()
    messages.success(request, 'Bloque eliminado.')
    return redirect('core:horarios')

@never_cache
@login_required
def horarios_api(request):
    """API JSON de horarios para el calendario."""
    from apps.usuarios.models import HorarioInstructor
    qs = HorarioInstructor.objects.select_related('instructor').all()
    data = [{'id': h.pk, 'instructor': h.instructor.nombre_completo,
             'fecha': str(h.fecha), 'hora_inicio': str(h.hora_inicio),
             'hora_fin': str(h.hora_fin), 'tipo': h.tipo,
             'descripcion': h.descripcion} for h in qs]
    return JsonResponse(data, safe=False)


# ═══════════════════════════════════════════════════════════════════
# NOTIFICACIONES IN-APP
# ═══════════════════════════════════════════════════════════════════
@never_cache
@login_required
def notificaciones(request):
    """Lista de todas las notificaciones del usuario."""
    from apps.usuarios.models import Notificacion
    notifs = Notificacion.objects.filter(usuario=request.user)
    return render(request, 'core/notificaciones.html', {'notificaciones': notifs})

@never_cache
@login_required
def leer_notificacion(request, pk):
    """Marcar una notificación como leída y redirigir a su URL."""
    from apps.usuarios.models import Notificacion
    n = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    n.leida = True
    n.save(update_fields=['leida'])
    return redirect(n.url or 'core:dashboard')

@never_cache
@login_required
def leer_todas(request):
    """Marcar todas las notificaciones como leídas."""
    from apps.usuarios.models import Notificacion
    Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
    messages.success(request,'Todas las notificaciones marcadas como leídas.')
    return redirect('core:notificaciones')

@never_cache
@login_required
def notif_conteo_api(request):
    """API JSON: devuelve el número de notificaciones no leídas."""
    from apps.usuarios.models import Notificacion
    count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    notifs = list(Notificacion.objects.filter(
        usuario=request.user, leida=False
    ).values('id','tipo','titulo','mensaje','url','created_at')[:5])
    return JsonResponse({'count': count, 'notificaciones': notifs})


# ═══════════════════════════════════════════════════════════════════
# MÉTRICAS GRÁFICAS (API JSON para Chart.js)
# ═══════════════════════════════════════════════════════════════════
@never_cache
@login_required
def metricas_api(request):
    """
    API JSON con datos para los gráficos del dashboard.
    Devuelve métricas de los últimos 6 meses.
    """
    import datetime
    from apps.asesorias.models import Asesoria
    from apps.elementos.models import ReservaEspacio, ReservaElemento
    from apps.usuarios.models import Usuario
    from django.db.models.functions import TruncMonth
    from django.db.models import Count

    hoy = datetime.date.today()
    hace6 = hoy - datetime.timedelta(days=180)

    # ── Asesorías por mes (últimos 6 meses) ────────────────────────
    asesorias_mes = (
        Asesoria.objects
        .filter(fecha__gte=hace6)
        .annotate(mes=TruncMonth('fecha'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )
    labels_asesorias = [a['mes'].strftime('%b %Y') for a in asesorias_mes]
    data_asesorias   = [a['total'] for a in asesorias_mes]

    # ── Reservas por mes ───────────────────────────────────────────
    reservas_mes = (
        ReservaEspacio.objects
        .filter(fecha_reserva__gte=hace6)
        .annotate(mes=TruncMonth('fecha_reserva'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )
    labels_reservas = [r['mes'].strftime('%b %Y') for r in reservas_mes]
    data_reservas   = [r['total'] for r in reservas_mes]

    # ── Asesorías por estado ───────────────────────────────────────
    por_estado = (
        Asesoria.objects
        .values('estado')
        .annotate(total=Count('id'))
    )
    estados_labels = [e['estado'] for e in por_estado]
    estados_data   = [e['total'] for e in por_estado]

    # ── Usuarios por rol ───────────────────────────────────────────
    from apps.usuarios.models import Rol, UsuarioRol
    roles_data = []
    for rol in Rol.objects.all():
        roles_data.append({
            'rol': rol.descripcion,
            'total': UsuarioRol.objects.filter(rol=rol).count()
        })

    # ── Asesorías por instructor ───────────────────────────────────
    por_instructor = (
        Asesoria.objects
        .values('usuario_asesor__nombres', 'usuario_asesor__apellidos')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )
    inst_labels = [f"{i['usuario_asesor__nombres']} {i['usuario_asesor__apellidos']}" for i in por_instructor]
    inst_data   = [i['total'] for i in por_instructor]

    return JsonResponse({
        'asesorias_por_mes': {
            'labels': labels_asesorias,
            'data':   data_asesorias,
        },
        'reservas_por_mes': {
            'labels': labels_reservas,
            'data':   data_reservas,
        },
        'asesorias_por_estado': {
            'labels': estados_labels,
            'data':   estados_data,
            'colores': ['#f47920','#3d9b35','#64748b','#a32d2d'],
        },
        'usuarios_por_rol': {
            'labels': [r['rol'] for r in roles_data],
            'data':   [r['total'] for r in roles_data],
        },
        'top_instructores': {
            'labels': inst_labels,
            'data':   inst_data,
        },
    })
