#!/usr/bin/env python
"""
verificar_entorno.py — BienestarMind SENA
Ejecutar antes de correr el servidor para verificar que todo esté configurado.
Uso: python verificar_entorno.py
"""
import sys
import os

OK   = "✅"
WARN = "⚠️ "
ERR  = "❌"
SEP  = "─" * 55

def check(label, fn):
    try:
        result = fn()
        print(f"  {OK} {label}{(' — ' + result) if result else ''}")
        return True
    except Exception as e:
        print(f"  {ERR} {label} → {e}")
        return False

errors = 0

print(f"\n{'🧠 BienestarMind SENA — Verificación del entorno':^55}")
print(SEP)

# Python version
print("\n📦 Python y dependencias")
v = sys.version_info
ok = check(f"Python {v.major}.{v.minor}.{v.micro}", lambda: None if v >= (3, 10) else (_ for _ in ()).throw(Exception("Se requiere Python 3.10+")))
if not ok: errors += 1

deps = ['django', 'psycopg2', 'reportlab', 'openpyxl', 'environ', 'crispy_forms', 'PIL', 'twilio']
for dep in deps:
    mod = dep if dep != 'PIL' else 'PIL'
    ok = check(f"Módulo {dep}", lambda m=mod: __import__(m) and None)
    if not ok: errors += 1

# .env
print("\n📄 Archivo .env")
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    print(f"  {OK} .env encontrado")
    with open(env_path) as f:
        content = f.read()
    keys = ['SECRET_KEY', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST']
    for k in keys:
        if k in content and f'{k}=' in content:
            val = [line.split('=', 1)[1].strip() for line in content.splitlines() if line.startswith(k + '=')]
            empty = not val or not val[0] or val[0] in ('', 'tu_password_aqui', 'tu_correo@gmail.com')
            status = WARN if empty else OK
            print(f"  {status} {k}{' (¡configurar!)' if empty else ''}")
    # APIs opcionales
    for k in ['EMAIL_HOST_USER', 'TWILIO_ACCOUNT_SID']:
        configured = k in content and 'xxxx' not in content
        print(f"  {'✅' if configured else '⚠️ '} {k}{' (opcional, sin configurar)' if not configured else ''}")
else:
    print(f"  {ERR} .env NO encontrado → copia .env.example como .env y configúralo")
    errors += 1

# PostgreSQL
print("\n🗄️  Base de datos")
try:
    import environ
    env = environ.Env()
    if os.path.exists(env_path):
        environ.Env.read_env(env_path)
    import psycopg2
    conn = psycopg2.connect(
        dbname=env('DB_NAME', default='db_bienestarmind'),
        user=env('DB_USER', default='postgres'),
        password=env('DB_PASSWORD', default='postgres'),
        host=env('DB_HOST', default='localhost'),
        port=env('DB_PORT', default='5432'),
        connect_timeout=3,
    )
    conn.close()
    print(f"  {OK} Conexión a PostgreSQL exitosa")
except Exception as e:
    print(f"  {ERR} No se pudo conectar a PostgreSQL → {e}")
    print(f"       Verifica que PostgreSQL esté corriendo y que .env tenga las credenciales correctas.")
    errors += 1

# Estructura de archivos
print("\n📁 Estructura del proyecto")
required = [
    'manage.py', 'requirements.txt', '.env.example',
    'bienestarmind/settings.py', 'bienestarmind/urls.py',
    'manage.py', 'requirements.txt', '.env.example',
    'apps/core/models.py', 'apps/core/context_processors.py',
    'apps/usuarios/models.py', 'apps/asesorias/models.py',
    'apps/elementos/models.py', 'apps/pqrs/models.py',
    'templates/base.html', 'templates/core/landing.html',
    'templates/core/calendario.html', 'templates/core/dashboard.html',
    'templates/usuarios/login.html', 'templates/usuarios/registro.html',
    'static/css/bienestarmind.css',
]
base = os.path.dirname(os.path.abspath(__file__))
for f in required:
    exists = os.path.exists(os.path.join(base, f))
    print(f"  {'✅' if exists else '❌'} {f}")
    if not exists: errors += 1

# Resumen
print(f"\n{SEP}")
if errors == 0:
    print(f"  🎉 ¡Todo listo! Ejecuta: python manage.py runserver")
    print(f"  🌐 Luego abre: http://127.0.0.1:8000/")
    print(f"  🔑 Admin: doc=0000000000 / pass=Admin2026*")
else:
    print(f"  {ERR} Se encontraron {errors} problema(s). Corrígelos antes de continuar.")
    print(f"  📖 Consulta el README.md para instrucciones detalladas.")
print(SEP + "\n")
