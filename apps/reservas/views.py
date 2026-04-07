"""
Vistas de Reservas (Espacios y Elementos) — BienestarMind
+ Conserva fecha/hora al editar
+ Admin/Coordinador pueden cambiar estado
+ Aprendiz/Instructor solo editan/eliminan lo suyo en PENDIENTE
+ Validación de disponibilidad
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django import forms
import datetime
from django.views.decorators.cache import never_cache

from apps.elementos.models import ReservaEspacio, ReservaElemento, Elemento
from apps.core.models import Espacio, Ficha
from apps.core.notificaciones import (
    notificar_reserva_espacio_completo,
    notificar_reserva_elemento_completo
)
from apps.reportes.generadores import (
    generar_pdf_reservas_espacios,
    generar_excel_reservas_espacios,
    generar_pdf_reservas_elementos,
    generar_excel_reservas_elementos,
)


# ── FORMS ──────────────────────────────────────────────────────────────────

class ReservaEspacioForm(forms.ModelForm):
    class Meta:
        model = ReservaEspacio
        fields = ['fecha_reserva', 'hora_inicio', 'duracion', 'espacio', 'ficha', 'motivo_reserva', 'estado']
        widgets = {
            'fecha_reserva': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'hora_inicio': forms.TimeInput(
                format='%H:%M',
                attrs={'class': 'form-control', 'type': 'time'}
            ),
            'duracion': forms.NumberInput(attrs={'class': 'form-control', 'min': 15, 'step': 15}),
            'espacio': forms.Select(attrs={'class': 'form-select'}),
            'ficha': forms.Select(attrs={'class': 'form-select'}),
            'motivo_reserva': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['ficha'].queryset = Ficha.objects.all()
        self.fields['ficha'].required = False
        self.fields['hora_inicio'].required = False
        self.fields['fecha_reserva'].input_formats = ['%Y-%m-%d']
        self.fields['hora_inicio'].input_formats = ['%H:%M']
        self.fields['fecha_reserva'].widget.attrs['min'] = datetime.date.today().isoformat()

        # Solo admin/coordinador pueden ver/cambiar el estado
        if not (user and user.tiene_rol('ADMINISTRADOR', 'COORDINADOR')):
            self.fields.pop('estado', None)
        else:
            self.fields['estado'].required = True

    def clean_fecha_reserva(self):
        fecha = self.cleaned_data.get('fecha_reserva')
        hoy = datetime.date.today()
        if fecha and fecha < hoy:
            raise forms.ValidationError(
                f'No puedes reservar un espacio en una fecha pasada. '
                f'Fecha mínima: {hoy.strftime("%d/%m/%Y")}. '
                f'Fecha ingresada: {fecha.strftime("%d/%m/%Y")}.'
            )
        return fecha

    def clean(self):
        cleaned = super().clean()
        espacio = cleaned.get('espacio')
        fecha = cleaned.get('fecha_reserva')
        hora_inicio = cleaned.get('hora_inicio')
        duracion = cleaned.get('duracion')

        if espacio and fecha:
            conflictos = ReservaEspacio.objects.filter(
                espacio=espacio,
                fecha_reserva=fecha,
                estado__in=['PENDIENTE', 'CONFIRMADA'],
            ).exclude(pk=self.instance.pk if self.instance.pk else None)

            if hora_inicio and duracion:
                hora_fin_nueva = (
                    datetime.datetime.combine(fecha, hora_inicio) +
                    datetime.timedelta(minutes=duracion)
                ).time()

                for reserva in conflictos:
                    if reserva.hora_inicio and reserva.duracion:
                        hora_fin_existente = (
                            datetime.datetime.combine(fecha, reserva.hora_inicio) +
                            datetime.timedelta(minutes=reserva.duracion)
                        ).time()

                        if hora_inicio < hora_fin_existente and hora_fin_nueva > reserva.hora_inicio:
                            raise forms.ValidationError(
                                f'El espacio "{espacio.nombre_del_espacio}" no está disponible '
                                f'el {fecha.strftime("%d/%m/%Y")} entre '
                                f'{reserva.hora_inicio.strftime("%H:%M")} y '
                                f'{hora_fin_existente.strftime("%H:%M")}.'
                            )
            elif conflictos.exists():
                raise forms.ValidationError(
                    f'El espacio "{espacio.nombre_del_espacio}" ya tiene una reserva '
                    f'para el {fecha.strftime("%d/%m/%Y")}.'
                )

        return cleaned


class ReservaElementoForm(forms.ModelForm):
    class Meta:
        model = ReservaElemento
        fields = ['fecha_reserva', 'elemento', 'ficha', 'descripcion_reserva', 'estado']
        widgets = {
            'fecha_reserva': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'elemento': forms.Select(attrs={'class': 'form-select'}),
            'ficha': forms.Select(attrs={'class': 'form-select'}),
            'descripcion_reserva': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        elemento_actual_id = self.instance.elemento_id if self.instance and self.instance.pk else None
        self.fields['elemento'].queryset = Elemento.objects.filter(
            Q(estado_elemento='DISPONIBLE') | Q(pk=elemento_actual_id)
        ).distinct()

        self.fields['ficha'].queryset = Ficha.objects.all()
        self.fields['ficha'].required = False
        self.fields['fecha_reserva'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_reserva'].widget.attrs['min'] = datetime.date.today().isoformat()

        # Solo admin/coordinador pueden ver/cambiar el estado
        if not (user and user.tiene_rol('ADMINISTRADOR', 'COORDINADOR')):
            self.fields.pop('estado', None)
        else:
            self.fields['estado'].required = True

    def clean_fecha_reserva(self):
        fecha = self.cleaned_data.get('fecha_reserva')
        hoy = datetime.date.today()
        if fecha and fecha < hoy:
            raise forms.ValidationError(
                f'No puedes solicitar un elemento para una fecha pasada. '
                f'Fecha mínima: {hoy.strftime("%d/%m/%Y")}. '
                f'Fecha ingresada: {fecha.strftime("%d/%m/%Y")}.'
            )
        return fecha

    def clean(self):
        cleaned = super().clean()
        elemento = cleaned.get('elemento')
        fecha = cleaned.get('fecha_reserva')

        if elemento and fecha:
            conflicto = ReservaElemento.objects.filter(
                elemento=elemento,
                fecha_reserva=fecha,
                estado__in=['PENDIENTE', 'APROBADA']
            ).exclude(pk=self.instance.pk if self.instance.pk else None).exists()

            if conflicto:
                raise forms.ValidationError(
                    f'El elemento "{elemento.nombre_elemento}" no está disponible '
                    f'para el {fecha.strftime("%d/%m/%Y")}.'
                )

        return cleaned


# ── HELPERS ────────────────────────────────────────────────────────────────

def _puede_editar_o_eliminar_reserva(usuario, reserva_usuario, estado):
    if usuario.tiene_rol('ADMINISTRADOR', 'COORDINADOR'):
        return True
    return (
        (usuario.es_aprendiz or usuario.es_instructor) and
        reserva_usuario == usuario and
        estado == 'PENDIENTE'
    )


# ── RESERVAS ESPACIOS ──────────────────────────────────────────────────────

@never_cache
@login_required
def lista_espacios(request):
    qs = ReservaEspacio.objects.select_related('espacio', 'espacio__sede', 'usuario', 'ficha').all()

    if request.user.es_aprendiz or request.user.es_instructor:
        qs = qs.filter(usuario=request.user)

    q = request.GET.get('q', '')
    estado = request.GET.get('estado', '')
    sede = request.GET.get('sede', '')
    f_d = request.GET.get('fecha_desde', '')
    f_h = request.GET.get('fecha_hasta', '')

    if q:
        qs = qs.filter(
            Q(motivo_reserva__icontains=q) |
            Q(espacio__nombre_del_espacio__icontains=q) |
            Q(usuario__nombres__icontains=q) |
            Q(usuario__apellidos__icontains=q)
        )
    if estado:
        qs = qs.filter(estado=estado)
    if sede:
        qs = qs.filter(espacio__sede__id=sede)
    if f_d:
        qs = qs.filter(fecha_reserva__gte=f_d)
    if f_h:
        qs = qs.filter(fecha_reserva__lte=f_h)

    if request.GET.get('formato') == 'pdf':
        buf = generar_pdf_reservas_espacios(qs)
        resp = HttpResponse(buf.read(), content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="reservas_espacios.pdf"'
        return resp

    if request.GET.get('formato') == 'excel':
        buf = generar_excel_reservas_espacios(qs)
        resp = HttpResponse(
            buf.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        resp['Content-Disposition'] = 'attachment; filename="reservas_espacios.xlsx"'
        return resp

    from apps.core.models import Sede
    return render(request, 'reservas/lista_espacios.html', {
        'reservas': qs,
        'estados': ReservaEspacio.ESTADO_CHOICES,
        'sedes': Sede.objects.all(),
        'q': q,
        'estado': estado,
        'sede': sede,
        'fecha_desde': f_d,
        'fecha_hasta': f_h,
        'total': qs.count(),
    })


@never_cache
@login_required
def crear_reserva_espacio(request):
    form = ReservaEspacioForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        reserva = form.save(commit=False)
        reserva.usuario = request.user

        if not request.user.tiene_rol('ADMINISTRADOR', 'COORDINADOR'):
            reserva.estado = 'PENDIENTE'
        elif not reserva.estado:
            reserva.estado = 'PENDIENTE'

        reserva.save()

        try:
            notificar_reserva_espacio_completo(reserva)
            messages.success(request, 'Espacio reservado. Notificaciones enviadas por email, SMS y WhatsApp.')
        except Exception:
            messages.success(request, 'Espacio reservado exitosamente.')

        return redirect('reservas:espacios')

    return render(request, 'reservas/form_espacio.html', {
        'form': form,
        'titulo': 'Reservar Espacio'
    })


@never_cache
@login_required
def editar_reserva_espacio(request, pk):
    reserva = get_object_or_404(ReservaEspacio, pk=pk)

    if not _puede_editar_o_eliminar_reserva(request.user, reserva.usuario, reserva.estado):
        messages.error(request, 'No tienes permisos para editar esta reserva.')
        return redirect('reservas:espacios')

    form = ReservaEspacioForm(request.POST or None, instance=reserva, user=request.user)

    if request.method == 'POST' and form.is_valid():
        reserva_editada = form.save(commit=False)
        reserva_editada.usuario = reserva.usuario

        if not request.user.tiene_rol('ADMINISTRADOR', 'COORDINADOR'):
            reserva_editada.estado = 'PENDIENTE'

        reserva_editada.save()
        messages.success(request, 'Reserva de espacio actualizada correctamente.')
        return redirect('reservas:espacios')

    return render(request, 'reservas/form_espacio.html', {
        'form': form,
        'titulo': f'Editar Reserva de Espacio #{reserva.pk}',
        'reserva': reserva,
    })


@never_cache
@login_required
def eliminar_reserva_espacio(request, pk):
    reserva = get_object_or_404(ReservaEspacio, pk=pk)

    if not _puede_editar_o_eliminar_reserva(request.user, reserva.usuario, reserva.estado):
        messages.error(request, 'No tienes permisos para eliminar esta reserva.')
        return redirect('reservas:espacios')

    reserva.delete()
    messages.success(request, 'Reserva eliminada correctamente.')
    return redirect('reservas:espacios')


# ── RESERVAS ELEMENTOS ─────────────────────────────────────────────────────

@never_cache
@login_required
def lista_elementos(request):
    qs = ReservaElemento.objects.select_related('elemento', 'elemento__categoria', 'usuario', 'ficha').all()

    if request.user.es_aprendiz or request.user.es_instructor:
        qs = qs.filter(usuario=request.user)

    q = request.GET.get('q', '')
    estado = request.GET.get('estado', '')

    if q:
        qs = qs.filter(
            Q(descripcion_reserva__icontains=q) |
            Q(elemento__nombre_elemento__icontains=q) |
            Q(usuario__nombres__icontains=q) |
            Q(usuario__apellidos__icontains=q)
        )
    if estado:
        qs = qs.filter(estado=estado)

    if request.GET.get('formato') == 'pdf':
        buf = generar_pdf_reservas_elementos(qs)
        resp = HttpResponse(buf.read(), content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="reservas_elementos.pdf"'
        return resp

    if request.GET.get('formato') == 'excel':
        buf = generar_excel_reservas_elementos(qs)
        resp = HttpResponse(
            buf.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        resp['Content-Disposition'] = 'attachment; filename="reservas_elementos.xlsx"'
        return resp

    return render(request, 'reservas/lista_elementos.html', {
        'reservas': qs,
        'estados': ReservaElemento.ESTADO_CHOICES,
        'q': q,
        'estado': estado,
        'total': qs.count(),
    })


@never_cache
@login_required
def crear_reserva_elemento(request):
    form = ReservaElementoForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        reserva = form.save(commit=False)
        reserva.usuario = request.user

        if not request.user.tiene_rol('ADMINISTRADOR', 'COORDINADOR'):
            reserva.estado = 'PENDIENTE'
        elif not reserva.estado:
            reserva.estado = 'PENDIENTE'

        reserva.save()

        try:
            notificar_reserva_elemento_completo(reserva)
            messages.success(request, 'Solicitud de elemento registrada. Notificaciones enviadas.')
        except Exception:
            messages.success(request, 'Solicitud de elemento registrada.')

        return redirect('reservas:elementos')

    return render(request, 'reservas/form_elemento.html', {
        'form': form,
        'titulo': 'Solicitar Elemento'
    })


@never_cache
@login_required
def editar_reserva_elemento(request, pk):
    reserva = get_object_or_404(ReservaElemento, pk=pk)

    if not _puede_editar_o_eliminar_reserva(request.user, reserva.usuario, reserva.estado):
        messages.error(request, 'No tienes permisos para editar esta reserva.')
        return redirect('reservas:elementos')

    form = ReservaElementoForm(request.POST or None, instance=reserva, user=request.user)

    if request.method == 'POST' and form.is_valid():
        reserva_editada = form.save(commit=False)
        reserva_editada.usuario = reserva.usuario

        if not request.user.tiene_rol('ADMINISTRADOR', 'COORDINADOR'):
            reserva_editada.estado = 'PENDIENTE'

        reserva_editada.save()

        # Si quedó aprobada, marca en uso
        if reserva_editada.estado == 'APROBADA' and reserva_editada.elemento:
            reserva_editada.elemento.estado_elemento = 'EN_USO'
            reserva_editada.elemento.save(update_fields=['estado_elemento'])

        # Si quedó cancelada o pendiente, libera si no tiene otras reservas activas
        elif reserva_editada.elemento and not ReservaElemento.objects.filter(
            elemento=reserva_editada.elemento,
            estado__in=['PENDIENTE', 'APROBADA']
        ).exclude(pk=reserva_editada.pk).exists():
            reserva_editada.elemento.estado_elemento = 'DISPONIBLE'
            reserva_editada.elemento.save(update_fields=['estado_elemento'])

        messages.success(request, 'Reserva de elemento actualizada correctamente.')
        return redirect('reservas:elementos')

    return render(request, 'reservas/form_elemento.html', {
        'form': form,
        'titulo': f'Editar Reserva de Elemento #{reserva.pk}',
        'reserva': reserva,
    })


@never_cache
@login_required
def eliminar_reserva_elemento(request, pk):
    reserva = get_object_or_404(ReservaElemento, pk=pk)

    if not _puede_editar_o_eliminar_reserva(request.user, reserva.usuario, reserva.estado):
        messages.error(request, 'No tienes permisos para eliminar esta reserva.')
        return redirect('reservas:elementos')

    elemento = reserva.elemento
    reserva.delete()

    if elemento and not ReservaElemento.objects.filter(
        elemento=elemento,
        estado__in=['PENDIENTE', 'APROBADA']
    ).exists():
        elemento.estado_elemento = 'DISPONIBLE'
        elemento.save(update_fields=['estado_elemento'])

    messages.success(request, 'Reserva de elemento eliminada correctamente.')
    return redirect('reservas:elementos')


@never_cache
@login_required
def aprobar_reserva_espacio(request, pk):
    if not request.user.tiene_rol('ADMINISTRADOR', 'COORDINADOR'):
        messages.error(request, 'No tienes permisos para aprobar reservas.')
        return redirect('reservas:espacios')

    reserva = get_object_or_404(ReservaEspacio, pk=pk)
    reserva.estado = 'CONFIRMADA'
    reserva.save()
    messages.success(request, f'Reserva #{pk} aprobada correctamente.')
    return redirect('reservas:espacios')


@never_cache
@login_required
def rechazar_reserva_espacio(request, pk):
    if not request.user.tiene_rol('ADMINISTRADOR', 'COORDINADOR'):
        messages.error(request, 'No tienes permisos para rechazar reservas.')
        return redirect('reservas:espacios')

    reserva = get_object_or_404(ReservaEspacio, pk=pk)
    reserva.estado = 'CANCELADA'
    reserva.save()
    messages.success(request, f'Reserva #{pk} rechazada.')
    return redirect('reservas:espacios')


@never_cache
@login_required
def aprobar_reserva_elemento(request, pk):
    if not request.user.tiene_rol('ADMINISTRADOR', 'COORDINADOR'):
        messages.error(request, 'No tienes permisos para aprobar reservas.')
        return redirect('reservas:elementos')

    reserva = get_object_or_404(ReservaElemento, pk=pk)
    reserva.estado = 'APROBADA'
    reserva.save()

    if reserva.elemento:
        reserva.elemento.estado_elemento = 'EN_USO'
        reserva.elemento.save(update_fields=['estado_elemento'])

    messages.success(request, f'Reserva #{pk} aprobada correctamente.')
    return redirect('reservas:elementos')


@never_cache
@login_required
def rechazar_reserva_elemento(request, pk):
    if not request.user.tiene_rol('ADMINISTRADOR', 'COORDINADOR'):
        messages.error(request, 'No tienes permisos para rechazar reservas.')
        return redirect('reservas:elementos')

    reserva = get_object_or_404(ReservaElemento, pk=pk)
    reserva.estado = 'CANCELADA'
    reserva.save()

    elemento = reserva.elemento
    if elemento and not ReservaElemento.objects.filter(
        elemento=elemento,
        estado__in=['PENDIENTE', 'APROBADA']
    ).exclude(pk=reserva.pk).exists():
        elemento.estado_elemento = 'DISPONIBLE'
        elemento.save(update_fields=['estado_elemento'])

    messages.success(request, f'Reserva #{pk} rechazada.')
    return redirect('reservas:elementos')