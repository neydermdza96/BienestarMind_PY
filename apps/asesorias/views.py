"""
Vistas de Asesorías — BienestarMind
+ Validación: no se permiten fechas pasadas (servidor + cliente)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django import forms
import datetime

from apps.asesorias.models import Asesoria
from apps.usuarios.models import Usuario
from apps.core.models import Ficha
from apps.core.notificaciones import notificar_asesoria_completo
from apps.reportes.generadores import generar_pdf_asesorias, generar_excel_asesorias


class AsesoriaForm(forms.ModelForm):
    class Meta:
        model = Asesoria
        fields = ['fecha', 'hora', 'motivo_asesoria', 'usuario_asesor', 'usuario_recibe', 'ficha', 'estado', 'observaciones']
        widgets = {
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'motivo_asesoria': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'usuario_asesor': forms.Select(attrs={'class': 'form-select'}),
            'usuario_recibe': forms.Select(attrs={'class': 'form-select'}),
            'ficha': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        instructores_roles = ['ADMINISTRADOR', 'INSTRUCTOR', 'COORDINADOR']
        self.fields['usuario_asesor'].queryset = Usuario.objects.filter(
            roles__descripcion__in=instructores_roles
        ).distinct()
        self.fields['usuario_recibe'].queryset = Usuario.objects.filter(is_active=True)
        self.fields['ficha'].queryset = Ficha.objects.all()
        self.fields['ficha'].required = False
        self.fields['hora'].required = False
        self.fields['observaciones'].required = False
        self.fields['estado'].required = False
        # Bloquear fechas pasadas en el selector del navegador (capa cliente)
        self.fields['fecha'].widget.attrs['min'] = datetime.date.today().isoformat()

    def clean_fecha(self):
        """Capa servidor: rechaza fechas anteriores a hoy aunque se manipule el HTML."""
        fecha = self.cleaned_data.get('fecha')
        hoy = datetime.date.today()
        if fecha and fecha < hoy:
            raise forms.ValidationError(
                f'No puedes registrar una asesoria en una fecha pasada. '
                f'Fecha minima permitida: {hoy.strftime("%d/%m/%Y")}. '
                f'Fecha ingresada: {fecha.strftime("%d/%m/%Y")}.'
            )
        return fecha


@login_required
def lista_asesorias(request):
    qs = Asesoria.objects.select_related('usuario_asesor', 'usuario_recibe', 'ficha').all()
    q = request.GET.get('q', '')
    estado = request.GET.get('estado', '')
    fecha_d = request.GET.get('fecha_desde', '')
    fecha_h = request.GET.get('fecha_hasta', '')
    if q:
        qs = qs.filter(
            Q(motivo_asesoria__icontains=q) |
            Q(usuario_asesor__nombres__icontains=q) | Q(usuario_asesor__apellidos__icontains=q) |
            Q(usuario_recibe__nombres__icontains=q) | Q(usuario_recibe__apellidos__icontains=q)
        )
    if estado: qs = qs.filter(estado=estado)
    if fecha_d: qs = qs.filter(fecha__gte=fecha_d)
    if fecha_h: qs = qs.filter(fecha__lte=fecha_h)
    if request.GET.get('formato') == 'pdf':
        buf = generar_pdf_asesorias(qs)
        resp = HttpResponse(buf.read(), content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="asesorias_bienestarmind.pdf"'
        return resp
    if request.GET.get('formato') == 'excel':
        buf = generar_excel_asesorias(qs)
        resp = HttpResponse(buf.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = 'attachment; filename="asesorias_bienestarmind.xlsx"'
        return resp
    return render(request, 'asesorias/lista.html', {
        'asesorias': qs, 'estados': Asesoria.ESTADO_CHOICES,
        'q': q, 'estado': estado, 'fecha_desde': fecha_d, 'fecha_hasta': fecha_h,
        'total': qs.count(),
    })


@login_required
def crear_asesoria(request):
    if not request.user.tiene_rol('ADMINISTRADOR', 'INSTRUCTOR', 'COORDINADOR'):
        messages.error(request, 'No tienes permisos para registrar asesorias.')
        return redirect('asesorias:lista')
    form = AsesoriaForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        asesoria = form.save(commit=False)
        asesoria.estado = 'CONFIRMADA'
        asesoria.save()
        try:
            notificar_asesoria_completo(asesoria)
            messages.success(request, 'Asesoria registrada. Notificaciones enviadas por email, SMS y WhatsApp.')
        except Exception:
            messages.success(request, 'Asesoria registrada. (Notificaciones en modo prueba)')
        return redirect('asesorias:lista')
    return render(request, 'asesorias/form.html', {'form': form, 'titulo': 'Registrar Asesoria'})


@login_required
def editar_asesoria(request, pk):
    asesoria = get_object_or_404(Asesoria, pk=pk)
    if not request.user.tiene_rol('ADMINISTRADOR', 'INSTRUCTOR', 'COORDINADOR'):
        messages.error(request, 'No tienes permisos.'); return redirect('asesorias:lista')
    form = AsesoriaForm(request.POST or None, instance=asesoria, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Asesoria actualizada.')
        return redirect('asesorias:lista')
    return render(request, 'asesorias/form.html', {'form': form, 'titulo': f'Editar Asesoria #{asesoria.pk}', 'asesoria': asesoria})


@login_required
def eliminar_asesoria(request, pk):
    if not request.user.tiene_rol('ADMINISTRADOR'):
        messages.error(request, 'Solo administradores pueden eliminar.'); return redirect('asesorias:lista')
    get_object_or_404(Asesoria, pk=pk).delete()
    messages.success(request, 'Asesoria eliminada.')
    return redirect('asesorias:lista')
