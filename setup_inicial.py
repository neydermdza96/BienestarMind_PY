"""
Script de datos iniciales — BienestarMind
Ejecutar con:  python manage.py shell < setup_inicial.py
O como comando: python manage.py shell -c "exec(open('setup_inicial.py').read())"
"""
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bienestarmind.settings')
django.setup()

from apps.usuarios.models import Rol, Usuario, UsuarioRol
from apps.core.models import Sede, Espacio, Programa, Ficha
from apps.elementos.models import CategoriaElemento, Elemento
import datetime

print("🌱 Cargando datos iniciales de BienestarMind...")

# ── Roles ──────────────────────────────────────────────────────────────────
roles_data = ['ADMINISTRADOR', 'INSTRUCTOR', 'APRENDIZ', 'COORDINADOR']
roles = {}
for r in roles_data:
    obj, created = Rol.objects.get_or_create(descripcion=r)
    roles[r] = obj
    print(f"  {'✅ Creado' if created else '⏭  Ya existe'}: Rol {r}")

# ── Sedes ──────────────────────────────────────────────────────────────────
sedes_data = [
    {'nombre_sede': 'SEDE SALITRE', 'telefono_sede': '7366060', 'direccion_sede': 'CRA 57 C # 64 29'},
    {'nombre_sede': 'SEDE CSF', 'telefono_sede': '5461600', 'direccion_sede': 'CRA 13 # 65 10'},
]
sedes = {}
for s in sedes_data:
    obj, created = Sede.objects.get_or_create(nombre_sede=s['nombre_sede'], defaults=s)
    sedes[s['nombre_sede']] = obj
    print(f"  {'✅ Creada' if created else '⏭  Ya existe'}: Sede {s['nombre_sede']}")

# ── Espacios ───────────────────────────────────────────────────────────────
espacios_data = [
    {'sede': 'SEDE SALITRE', 'nombre': 'Sala Bienestar Principal', 'cap': 15},
    {'sede': 'SEDE SALITRE', 'nombre': 'Consultorio Psicología 1', 'cap': 3},
    {'sede': 'SEDE SALITRE', 'nombre': 'Consultorio Psicología 2', 'cap': 3},
    {'sede': 'SEDE CSF',     'nombre': 'Sala Bienestar CSF', 'cap': 12},
    {'sede': 'SEDE CSF',     'nombre': 'Consultorio Orientación', 'cap': 4},
]
for e in espacios_data:
    sede = sedes.get(e['sede'])
    if sede:
        obj, created = Espacio.objects.get_or_create(
            sede=sede, nombre_del_espacio=e['nombre'],
            defaults={'capacidad': e['cap']}
        )
        print(f"  {'✅ Creado' if created else '⏭  Ya existe'}: Espacio {e['nombre']}")

# ── Programas y Fichas ─────────────────────────────────────────────────────
programas_data = [
    (1, 'Tecnólogo en Análisis y Desarrollo de Software', 'Diseño y desarrollo de sistemas de información.'),
    (2, 'Técnico en Sistemas', 'Instalación y soporte técnico de software y hardware.'),
    (3, 'Gestión de Redes de Datos', 'Configuración y mantenimiento de infraestructuras de red.'),
    (4, 'Multimedia y Diseño Web', 'Creación de contenido digital y sitios web interactivos.'),
    (5, 'Programación de Software', 'Desarrollo de aplicaciones de escritorio y móviles.'),
    (6, 'Seguridad Informática', 'Protección de activos de información y defensa ante ataques.'),
]
programas = {}
for pid, nombre, desc in programas_data:
    obj, created = Programa.objects.get_or_create(id=pid, defaults={'nombre_programa': nombre, 'descripcion': desc})
    programas[pid] = obj
    print(f"  {'✅ Creado' if created else '⏭  Ya existe'}: Programa {nombre[:40]}")

fichas_data = [
    (3065830, 'Tecnología en Análisis y Desarrollo de Software', 'DIURNA', 1),
    (3080485, 'Técnico en Sistemas', 'MANANA', 2),
    (2825640, 'Gestión de Redes de Datos', 'NOCTURNA', 3),
    (2901235, 'Multimedia y Diseño Web', 'MIXTA', 4),
    (3104567, 'Programación de Software', 'TARDE', 5),
    (2758901, 'Seguridad Informática', 'DIURNA', 6),
]
for fid, desc, jornada, prog_id in fichas_data:
    obj, created = Ficha.objects.get_or_create(
        id_ficha=fid,
        defaults={'descripcion': desc, 'jornada_ficha': jornada, 'programa': programas[prog_id]}
    )
    print(f"  {'✅ Creada' if created else '⏭  Ya existe'}: Ficha {fid}")

# ── Categorías de elementos ────────────────────────────────────────────────
cats_data = ['Equipos de Cómputo', 'Material Didáctico', 'Equipos Audiovisuales', 'Mobiliario']
cats = {}
for c in cats_data:
    obj, created = CategoriaElemento.objects.get_or_create(descripcion=c)
    cats[c] = obj
    print(f"  {'✅ Creada' if created else '⏭  Ya existe'}: Categoría {c}")

# ── Elementos ──────────────────────────────────────────────────────────────
elementos_data = [
    ('Portátil Lenovo ThinkPad', 'Equipos de Cómputo', 'DISPONIBLE', 'BM-PC-001'),
    ('Tablet Samsung A8', 'Equipos de Cómputo', 'DISPONIBLE', 'BM-PC-002'),
    ('Kit de Relajación Mindfulness', 'Material Didáctico', 'DISPONIBLE', 'BM-MD-001'),
    ('Proyector EPSON X49', 'Equipos Audiovisuales', 'DISPONIBLE', 'BM-AV-001'),
    ('Parlante Bluetooth JBL', 'Equipos Audiovisuales', 'DISPONIBLE', 'BM-AV-002'),
]
for nombre, cat, estado, codigo in elementos_data:
    obj, created = Elemento.objects.get_or_create(
        codigo=codigo,
        defaults={'nombre_elemento': nombre, 'categoria': cats[cat], 'estado_elemento': estado}
    )
    print(f"  {'✅ Creado' if created else '⏭  Ya existe'}: Elemento {nombre}")

# ── Superusuario administrador ─────────────────────────────────────────────
if not Usuario.objects.filter(documento='0000000000').exists():
    admin = Usuario.objects.create_user(
        documento='0000000000',
        password='Admin2026*',
        nombres='ADMINISTRADOR',
        apellidos='BIENESTARMIND',
        correo='admin@bienestarmind.sena.edu.co',
        genero='NO_ESPECIFICA',
        fecha_de_nacimiento=datetime.date(1990, 1, 1),
        is_staff=True,
        is_superuser=True,
    )
    UsuarioRol.objects.create(usuario=admin, rol=roles['ADMINISTRADOR'])
    print("  ✅ Creado: Superusuario admin (doc: 0000000000 / pass: Admin2026*)")
else:
    print("  ⏭  Ya existe: Superusuario admin")

print("\n🎉 ¡Datos iniciales cargados exitosamente!")
print("\n📋 Acceso rápido:")
print("   URL:      http://127.0.0.1:8000/")
print("   Documento: 0000000000")
print("   Contraseña: Admin2026*")
print("\n💡 Recuerda configurar tu .env con las credenciales de email y Twilio")
