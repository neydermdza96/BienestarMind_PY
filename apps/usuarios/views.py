"""
Vistas de Usuarios — BienestarMind
- Login / Logout con sesión segura
- Registro público de nuevos usuarios (solo Aprendiz por defecto)
- Recuperación de contraseña por email con token de un solo uso
- CRUD de usuarios (admin)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.decorators.cache import never_cache
import datetime

from apps.usuarios.models import Usuario, Rol, UsuarioRol, TokenRecuperacion
from apps.reportes.generadores import generar_pdf_usuarios, generar_excel_usuarios


# ════════════════════════════════════════════════════════════════════
# FORMULARIOS
# ════════════════════════════════════════════════════════════════════

class LoginForm(forms.Form):
    username = forms.CharField(
        label='Documento', max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de documento'}),
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )


class RegistroForm(forms.ModelForm):
    """
    Formulario público de registro.
    Asigna el rol APRENDIZ automáticamente.
    Valida edad mínima y contraseña con confirmación.
    """
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo 8 caracteres'}),
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repite la contraseña'}),
    )

    class Meta:
        model = Usuario
        fields = ['nombres', 'apellidos', 'documento', 'correo', 'genero', 'telefono', 'fecha_de_nacimiento']
        widgets = {
            'nombres':             forms.TextInput(attrs={'class': 'form-control', 'style': 'text-transform:uppercase', 'placeholder': 'Ej: JUAN CARLOS'}),
            'apellidos':           forms.TextInput(attrs={'class': 'form-control', 'style': 'text-transform:uppercase', 'placeholder': 'Ej: RODRIGUEZ'}),
            'documento':           forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cédula o TI'}),
            'correo':              forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'genero':              forms.Select(attrs={'class': 'form-select'}),
            'telefono':            forms.TextInput(attrs={'class': 'form-control', 'placeholder': '3XXXXXXXXX'}),
            'fecha_de_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean_nombres(self):
        return self.cleaned_data.get('nombres', '').upper()

    def clean_apellidos(self):
        return self.cleaned_data.get('apellidos', '').upper()

    def clean_fecha_de_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_de_nacimiento')
        if fecha:
            hoy  = datetime.date.today()
            edad = (hoy - fecha).days // 365
            edad_min = getattr(settings, 'EDAD_MINIMA', 16)
            if edad < edad_min:
                raise forms.ValidationError(
                    f'Debes tener al menos {edad_min} años para registrarte. '
                    f'Tu edad calculada es {edad} año{"s" if edad != 1 else ""}.'
                )
        return fecha

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1', '')
        p2 = self.cleaned_data.get('password2', '')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        if len(p1) < 8:
            raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres.')
        return p2


class RecuperarPasswordForm(forms.Form):
    correo = forms.EmailField(
        label='Correo electrónico registrado',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu@correo.com'}),
    )


class NuevaPasswordForm(forms.Form):
    password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo 8 caracteres'}),
    )
    password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repite la nueva contraseña'}),
    )

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1', '')
        p2 = self.cleaned_data.get('password2', '')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        if len(p1) < 8:
            raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres.')
        return p2


class UsuarioForm(forms.ModelForm):
    password = forms.CharField(
        label='Contraseña', required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Dejar vacío para no cambiar'}),
        help_text='Mínimo 8 caracteres. Dejar vacío para mantener la contraseña actual.',
    )
    roles = forms.ModelMultipleChoiceField(
        queryset=Rol.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True, label='Roles',
    )

    class Meta:
        model = Usuario
        fields = ['nombres', 'apellidos', 'documento', 'correo', 'genero', 'telefono', 'fecha_de_nacimiento', 'foto']
        widgets = {
            'nombres':             forms.TextInput(attrs={'class': 'form-control', 'style': 'text-transform:uppercase'}),
            'apellidos':           forms.TextInput(attrs={'class': 'form-control', 'style': 'text-transform:uppercase'}),
            'documento':           forms.TextInput(attrs={'class': 'form-control'}),
            'correo':              forms.EmailInput(attrs={'class': 'form-control'}),
            'genero':              forms.Select(attrs={'class': 'form-select'}),
            'telefono':            forms.TextInput(attrs={'class': 'form-control', 'placeholder': '3XXXXXXXXX'}),
            'fecha_de_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'foto':                forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_fecha_de_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_de_nacimiento')
        if fecha:
            hoy  = datetime.date.today()
            edad = (hoy - fecha).days // 365
            edad_min = getattr(settings, 'EDAD_MINIMA', 16)
            if edad < edad_min:
                raise forms.ValidationError(
                    f'El usuario debe tener al menos {edad_min} años. '
                    f'Edad calculada: {edad} año{"s" if edad != 1 else ""}.'
                )
        return fecha

    def clean_nombres(self):
        return self.cleaned_data.get('nombres', '').upper()

    def clean_apellidos(self):
        return self.cleaned_data.get('apellidos', '').upper()


# ════════════════════════════════════════════════════════════════════
# HELPERS PRIVADOS
# ════════════════════════════════════════════════════════════════════

def _enviar_email_recuperacion(usuario, token, request):
    """Construye y envía el email con el enlace de recuperación."""
    from django.urls import reverse
    enlace = request.build_absolute_uri(
        reverse('usuarios:nueva_password', kwargs={'token': str(token.token)})
    )
    contexto = {
        'usuario': usuario,
        'enlace': enlace,
        'horas_validez': TokenRecuperacion.HORAS_VALIDEZ,
    }
    try:
        html_msg   = render_to_string('emails/recuperar_password.html', contexto)
        plain_msg  = strip_tags(html_msg)
        send_mail(
            subject='Recuperación de contraseña — BienestarMind SENA',
            message=plain_msg,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.correo],
            html_message=html_msg,
            fail_silently=False,
        )
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'Error enviando email recuperación: {e}')
        return False


def _enviar_email_bienvenida(usuario, request):
    """Email de bienvenida al registrarse."""
    contexto = {'usuario': usuario}
    try:
        html_msg  = render_to_string('emails/bienvenida.html', contexto)
        plain_msg = strip_tags(html_msg)
        send_mail(
            subject='Bienvenido a BienestarMind — SENA',
            message=plain_msg,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.correo],
            html_message=html_msg,
            fail_silently=True,
        )
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════════
# VISTAS DE AUTENTICACIÓN
# ════════════════════════════════════════════════════════════════════

def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        doc = form.cleaned_data['username']
        pwd = form.cleaned_data['password']
        user = authenticate(request, username=doc, password=pwd)
        if user is not None:
            if not user.is_active:
                messages.error(request, 'Tu cuenta está desactivada. Contacta al administrador.')
            else:
                login(request, user)
                request.session.cycle_key()
                messages.success(request, f'Bienvenido, {user.nombres}')
                return redirect(request.GET.get('next', 'core:dashboard'))
        else:
            messages.error(request, 'Documento o contraseña incorrectos.')
    return render(request, 'usuarios/login.html', {
        'form': form,
        'year': datetime.date.today().year,
    })


def logout_view(request):
    logout(request)
    messages.info(request, 'Sesión cerrada exitosamente.')
    return redirect('usuarios:login')


# ════════════════════════════════════════════════════════════════════
# REGISTRO PÚBLICO
# ════════════════════════════════════════════════════════════════════

def registro_view(request):
    """
    Registro público. Cualquier persona puede registrarse como APRENDIZ.
    El administrador puede cambiar el rol después si es necesario.
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        pwd = form.cleaned_data['password1']
        user.save()
        user.set_password(pwd)
        user.save()

        # Asignar rol APRENDIZ por defecto
        try:
            rol_aprendiz = Rol.objects.get(descripcion='APRENDIZ')
            UsuarioRol.objects.create(usuario=user, rol=rol_aprendiz)
        except Rol.DoesNotExist:
            pass

        # Email de bienvenida
        _enviar_email_bienvenida(user, request)

        messages.success(
            request,
            f'Cuenta creada exitosamente. Bienvenido, {user.nombres}. '
            f'Ya puedes iniciar sesión con tu documento y contraseña.'
        )
        return redirect('usuarios:login')

    return render(request, 'usuarios/registro.html', {
        'form': form,
        'year': datetime.date.today().year,
    })


# ════════════════════════════════════════════════════════════════════
# RECUPERACIÓN DE CONTRASEÑA
# ════════════════════════════════════════════════════════════════════

def recuperar_password(request):
    """
    Paso 1: el usuario ingresa su correo.
    Si existe, generamos un token y enviamos el email.
    Por seguridad, siempre mostramos el mismo mensaje (no revelamos
    si el correo existe o no en el sistema).
    """
    form = RecuperarPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        correo = form.cleaned_data['correo'].lower().strip()
        try:
            usuario = Usuario.objects.get(correo__iexact=correo, is_active=True)
            # Invalidar tokens anteriores del usuario
            TokenRecuperacion.objects.filter(usuario=usuario, usado=False).update(usado=True)
            # Crear nuevo token
            token = TokenRecuperacion.objects.create(usuario=usuario)
            # Enviar email
            _enviar_email_recuperacion(usuario, token, request)
        except Usuario.DoesNotExist:
            pass  # No revelar si el correo existe
        # Siempre redirigir a "enviado" para no revelar si existe
        return redirect('usuarios:recuperar_enviado')

    return render(request, 'usuarios/recuperar_password.html', {
        'form': form,
        'year': datetime.date.today().year,
    })


def recuperar_enviado(request):
    """Paso 2: confirmación de que el email fue enviado."""
    return render(request, 'usuarios/recuperar_enviado.html', {
        'year': datetime.date.today().year,
    })


def nueva_password(request, token):
    """
    Paso 3: el usuario llega desde el enlace del email.
    Verifica que el token sea válido, no usado y no expirado.
    """
    try:
        tok = TokenRecuperacion.objects.get(token=token)
    except TokenRecuperacion.DoesNotExist:
        return render(request, 'usuarios/token_invalido.html', {'razon': 'El enlace no es válido.'})

    if not tok.valido:
        razon = 'El enlace ya fue utilizado.' if tok.usado else f'El enlace expiró (válido {TokenRecuperacion.HORAS_VALIDEZ} horas).'
        return render(request, 'usuarios/token_invalido.html', {'razon': razon})

    form = NuevaPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = tok.usuario
        usuario.set_password(form.cleaned_data['password1'])
        usuario.save()
        # Marcar token como usado
        tok.usado = True
        tok.save()
        # Invalidar cualquier otro token pendiente
        TokenRecuperacion.objects.filter(usuario=usuario, usado=False).update(usado=True)
        return redirect('usuarios:password_confirmado')

    return render(request, 'usuarios/nueva_password.html', {
        'form': form,
        'token': token,
        'usuario': tok.usuario,
        'year': datetime.date.today().year,
    })


def password_confirmado(request):
    """Paso 4: confirmación de contraseña cambiada exitosamente."""
    return render(request, 'usuarios/password_confirmado.html', {
        'year': datetime.date.today().year,
    })


# ════════════════════════════════════════════════════════════════════
# GESTIÓN DE USUARIOS (ADMIN)
# ════════════════════════════════════════════════════════════════════
@never_cache
@login_required
def lista_usuarios(request):
    qs = Usuario.objects.prefetch_related('roles').all()
    q      = request.GET.get('q', '')
    rol_id = request.GET.get('rol', '')
    genero = request.GET.get('genero', '')
    if q:
        qs = qs.filter(
            Q(nombres__icontains=q) | Q(apellidos__icontains=q) |
            Q(documento__icontains=q) | Q(correo__icontains=q) |
            Q(telefono__icontains=q)
        )
    if rol_id: qs = qs.filter(roles__id=rol_id)
    if genero: qs = qs.filter(genero=genero)
    if request.GET.get('formato') == 'pdf':
        buf  = generar_pdf_usuarios(qs)
        resp = HttpResponse(buf.read(), content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="usuarios_bienestarmind.pdf"'
        return resp
    if request.GET.get('formato') == 'excel':
        buf  = generar_excel_usuarios(qs)
        resp = HttpResponse(buf.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        resp['Content-Disposition'] = 'attachment; filename="usuarios_bienestarmind.xlsx"'
        return resp
    return render(request, 'usuarios/lista.html', {
        'usuarios': qs,
        'roles': Rol.objects.all(),
        'q': q, 'rol_id': rol_id, 'genero': genero,
        'total': qs.count(),
    })

@never_cache
@login_required
def crear_usuario(request):
    if not request.user.tiene_rol('ADMINISTRADOR', 'COORDINADOR'):
        messages.error(request, 'No tienes permisos para crear usuarios.')
        return redirect('usuarios:lista')
    form = UsuarioForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        pwd = form.cleaned_data.get('password')
        user.set_password(pwd if pwd else user.documento)
        user.save()
        for rol in form.cleaned_data['roles']:
            UsuarioRol.objects.create(usuario=user, rol=rol)
        messages.success(request, f'Usuario {user.nombre_completo} creado exitosamente.')
        return redirect('usuarios:lista')
    return render(request, 'usuarios/form.html', {
        'form': form, 'titulo': 'Nuevo Usuario', 'accion': 'Crear',
    })

@never_cache
@login_required
def editar_usuario(request, pk):
    usuario    = get_object_or_404(Usuario, pk=pk)
    es_admin   = request.user.tiene_rol('ADMINISTRADOR', 'COORDINADOR')
    es_propio  = request.user.pk == pk
    if not (es_admin or es_propio):
        messages.error(request, 'No tienes permisos para editar este usuario.')
        return redirect('usuarios:lista')
    initial_roles = list(usuario.roles.values_list('id', flat=True))
    form = UsuarioForm(request.POST or None, request.FILES or None,
                       instance=usuario, initial={'roles': initial_roles})
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        pwd = form.cleaned_data.get('password')
        if pwd:
            user.set_password(pwd)
        user.save()
        if es_admin:
            usuario.usuario_roles.all().delete()
            for rol in form.cleaned_data['roles']:
                UsuarioRol.objects.get_or_create(usuario=user, rol=rol)
        messages.success(request, 'Usuario actualizado correctamente.')
        return redirect('usuarios:lista')
    return render(request, 'usuarios/form.html', {
        'form': form,
        'titulo': f'Editar: {usuario.nombre_completo}',
        'accion': 'Guardar cambios',
        'usuario': usuario,
    })

@never_cache
@login_required
def toggle_usuario(request, pk):
    if not request.user.tiene_rol('ADMINISTRADOR'):
        messages.error(request, 'Acción no permitida.')
        return redirect('usuarios:lista')
    usuario = get_object_or_404(Usuario, pk=pk)
    if usuario.pk == request.user.pk:
        messages.error(request, 'No puedes desactivar tu propia cuenta.')
        return redirect('usuarios:lista')
    usuario.is_active = not usuario.is_active
    usuario.save()
    estado = 'activado' if usuario.is_active else 'desactivado'
    messages.success(request, f'Usuario {usuario.nombre_completo} {estado}.')
    return redirect('usuarios:lista')
