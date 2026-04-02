"""
Vistas PQRS — BienestarMind
Peticiones, Quejas, Reclamos, Sugerencias y Felicitaciones
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django import forms
from django.views.decorators.cache import never_cache

from apps.pqrs.models import PQRS


# ── FORMULARIOS ────────────────────────────────────────────────────

class PQRSForm(forms.ModelForm):
    class Meta:
        model  = PQRS
        fields = ['tipo','asunto','descripcion','nombre_anonimo','correo_contacto']
        widgets = {
            'tipo':           forms.Select(attrs={'class':'form-select'}),
            'asunto':         forms.TextInput(attrs={'class':'form-control','placeholder':'Resumen breve del asunto'}),
            'descripcion':    forms.Textarea(attrs={'class':'form-control','rows':5,'placeholder':'Describe detalladamente tu solicitud, queja, reclamo, sugerencia o felicitación...'}),
            'nombre_anonimo': forms.TextInput(attrs={'class':'form-control','placeholder':'Tu nombre (si no estás registrado)'}),
            'correo_contacto':forms.EmailInput(attrs={'class':'form-control','placeholder':'correo@ejemplo.com para recibir respuesta'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.is_authenticated:
            self.fields['nombre_anonimo'].widget = forms.HiddenInput()
            self.fields['correo_contacto'].initial = self.user.correo
            self.fields['nombre_anonimo'].required = False
        else:
            self.fields['nombre_anonimo'].required = False
            self.fields['correo_contacto'].required = False


class RespuestaForm(forms.Form):
    respuesta = forms.CharField(
        label='Respuesta',
        widget=forms.Textarea(attrs={'class':'form-control','rows':5,'placeholder':'Escribe la respuesta oficial a esta PQRS...'}),
    )
    estado    = forms.ChoiceField(
        label='Cambiar estado a',
        choices=PQRS.ESTADO_CHOICES,
        widget=forms.Select(attrs={'class':'form-select'}),
    )
    prioridad = forms.ChoiceField(
        label='Prioridad',
        choices=PQRS.PRIORIDAD_CHOICES,
        widget=forms.Select(attrs={'class':'form-select'}),
    )


# ── VISTAS PÚBLICAS ────────────────────────────────────────────────

def crear_pqrs(request):
    """Cualquier persona (logueada o no) puede enviar una PQRS."""
    form = PQRSForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        pqrs = form.save(commit=False)
        if request.user.is_authenticated:
            pqrs.usuario = request.user
            pqrs.correo_contacto = pqrs.correo_contacto or request.user.correo
        pqrs.save()
        # Notificar por email si tiene correo
        if pqrs.correo_contacto:
            _enviar_confirmacion(pqrs)
        return redirect('pqrs:enviado')
    # Stats para mostrar en el formulario
    stats = {
        'total':       PQRS.objects.count(),
        'respondidas': PQRS.objects.filter(estado='RESPONDIDA').count(),
        'tiempo_resp': '48 horas hábiles',
    }
    return render(request, 'pqrs/crear.html', {'form': form, 'stats': stats})


def enviado(request):
    return render(request, 'pqrs/enviado.html')

@never_cache
@login_required
def mis_pqrs(request):
    """El usuario logueado ve sus propias PQRS."""
    qs = PQRS.objects.filter(usuario=request.user)
    return render(request, 'pqrs/mis_pqrs.html', {'pqrs_list': qs})


# ── VISTAS ADMIN ───────────────────────────────────────────────────
@never_cache
@login_required
def lista_admin(request):
    """Administradores y Coordinadores ven y gestionan todas las PQRS."""
    if not request.user.tiene_rol('ADMINISTRADOR','COORDINADOR'):
        messages.error(request,'Acceso restringido.'); return redirect('core:dashboard')

    qs = PQRS.objects.select_related('usuario','respondida_por').all()
    q      = request.GET.get('q','')
    tipo   = request.GET.get('tipo','')
    estado = request.GET.get('estado','')

    if q:      qs = qs.filter(Q(asunto__icontains=q)|Q(descripcion__icontains=q)|Q(radicado__icontains=q))
    if tipo:   qs = qs.filter(tipo=tipo)
    if estado: qs = qs.filter(estado=estado)

    resumen = {
        'total':       PQRS.objects.count(),
        'pendientes':  PQRS.objects.filter(estado='PENDIENTE').count(),
        'en_revision': PQRS.objects.filter(estado='EN_REVISION').count(),
        'respondidas': PQRS.objects.filter(estado='RESPONDIDA').count(),
    }
    por_tipo = {t[0]: PQRS.objects.filter(tipo=t[0]).count() for t in PQRS.TIPO_CHOICES}

    return render(request,'pqrs/lista_admin.html',{
        'pqrs_list': qs, 'resumen': resumen, 'por_tipo': por_tipo,
        'tipos': PQRS.TIPO_CHOICES, 'estados': PQRS.ESTADO_CHOICES,
        'q':q,'tipo':tipo,'estado':estado,'total':qs.count(),
    })

@never_cache
@login_required
def detalle_pqrs(request, pk):
    if not request.user.tiene_rol('ADMINISTRADOR','COORDINADOR'):
        messages.error(request,'Acceso restringido.'); return redirect('core:dashboard')
    pqrs = get_object_or_404(PQRS, pk=pk)
    # Marcar en revisión automáticamente al abrir
    if pqrs.estado == 'PENDIENTE':
        pqrs.estado = 'EN_REVISION'
        pqrs.save(update_fields=['estado'])
    return render(request,'pqrs/detalle.html',{'pqrs': pqrs})

@never_cache
@login_required
def responder_pqrs(request, pk):
    if not request.user.tiene_rol('ADMINISTRADOR','COORDINADOR'):
        messages.error(request,'Acceso restringido.'); return redirect('core:dashboard')
    pqrs = get_object_or_404(PQRS, pk=pk)
    form = RespuestaForm(request.POST or None, initial={
        'estado': pqrs.estado, 'prioridad': pqrs.prioridad
    })
    if request.method == 'POST' and form.is_valid():
        pqrs.respuesta       = form.cleaned_data['respuesta']
        pqrs.estado          = form.cleaned_data['estado']
        pqrs.prioridad       = form.cleaned_data['prioridad']
        pqrs.respondida_por  = request.user
        pqrs.fecha_respuesta = timezone.now()
        pqrs.save()
        if pqrs.correo_contacto:
            _enviar_respuesta(pqrs)
        messages.success(request, f'PQRS {pqrs.radicado} respondida correctamente.')
        return redirect('pqrs:admin')
    return render(request,'pqrs/responder.html',{'form':form,'pqrs':pqrs})


def _enviar_confirmacion(pqrs):
    from django.core.mail import send_mail
    from django.conf import settings
    try:
        send_mail(
            subject=f'PQRS recibida — Radicado {pqrs.radicado} — BienestarMind SENA',
            message=f'Hola {pqrs.nombre_remitente},\n\nHemos recibido tu {pqrs.get_tipo_display()} con radicado {pqrs.radicado}.\nAsunto: {pqrs.asunto}\n\nDaremos respuesta en máximo 48 horas hábiles.\n\nBienestarMind SENA',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[pqrs.correo_contacto],
            fail_silently=True,
        )
    except Exception: pass


def _enviar_respuesta(pqrs):
    from django.core.mail import send_mail
    from django.conf import settings
    try:
        send_mail(
            subject=f'Respuesta a tu PQRS {pqrs.radicado} — BienestarMind SENA',
            message=f'Hola {pqrs.nombre_remitente},\n\nTu {pqrs.get_tipo_display()} (Radicado: {pqrs.radicado}) ha sido respondida:\n\n{pqrs.respuesta}\n\nEstado: {pqrs.get_estado_display()}\n\nBienestarMind SENA',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[pqrs.correo_contacto],
            fail_silently=True,
        )
    except Exception: pass
