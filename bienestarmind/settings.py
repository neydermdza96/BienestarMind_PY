"""
BienestarMind — Configuración principal Django
Proyecto SENA · Tecnólogo ADSO
"""
import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, True))
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY', default='django-insecure-bienestarmind-sena-2026-change-in-prod')
DEBUG = env('DEBUG', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_extensions',
    'apps.core',
    'apps.usuarios',
    'apps.asesorias',
    'apps.reservas',
    'apps.elementos',
    'apps.reportes',
    'apps.pqrs',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bienestarmind.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.sena_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'bienestarmind.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='db_bienestarmind'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default='postgres'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

AUTH_USER_MODEL = 'usuarios.Usuario'

# ── Encriptación de contraseñas ────────────────────────────────────────────
# Django usa PBKDF2 + SHA256 + salt aleatorio por defecto.
# Aquí se declara el orden de algoritmos preferidos (el primero es el activo).
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',   # activo — más seguro
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.ScryptPasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

LOGIN_URL = '/usuarios/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/usuarios/login/'

# ── Email ──────────────────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = 'BienestarMind SENA <noreply@bienestarmind.sena.edu.co>'

# ── Twilio ─────────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = env('TWILIO_PHONE_NUMBER', default='')
TWILIO_WHATSAPP_NUMBER = env('TWILIO_WHATSAPP_NUMBER', default='whatsapp:+14155238886')

# ── Edad mínima ────────────────────────────────────────────────────────────
EDAD_MINIMA = 16

# ── SEGURIDAD DE SESIONES ──────────────────────────────────────────────────
# Las sesiones expiran a las 8 horas de inactividad
SESSION_COOKIE_AGE = 28800

# CLAVE: la sesión se destruye al cerrar el navegador
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# La sesión NO se renueva automáticamente con cada request.
# Así, si alguien copia la URL y la abre en otra pestaña/navegador,
# cada dispositivo necesita su propia sesión autenticada.
SESSION_SAVE_EVERY_REQUEST = False

# La cookie de sesión solo se envía por HTTPS en producción
SESSION_COOKIE_SECURE = not DEBUG

# La cookie no es accesible desde JavaScript (protección XSS)
SESSION_COOKIE_HTTPONLY = True

# Protección CSRF: la cookie solo se envía en requests del mismo sitio
SESSION_COOKIE_SAMESITE = 'Lax'

# Nombre personalizado de la cookie (oscuridad adicional)
SESSION_COOKIE_NAME = 'bm_session'

# CSRF también solo por HTTPS en producción
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# Cabeceras de seguridad adicionales
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
