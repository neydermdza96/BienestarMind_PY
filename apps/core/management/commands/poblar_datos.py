"""
Comando Django para poblar datos iniciales
Uso: python manage.py poblar_datos
"""
from django.core.management.base import BaseCommand
from django.db import transaction
import datetime


class Command(BaseCommand):
    help = 'Pobla la base de datos con datos iniciales de BienestarMind'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🌱 Iniciando carga de datos...'))
        with transaction.atomic():
            self._crear_roles()
            self._crear_sedes()
            self._crear_programas_fichas()
            self._crear_categorias_elementos()
            self._crear_superusuario()
        self.stdout.write(self.style.SUCCESS('\n🎉 ¡Datos cargados exitosamente!'))
        self.stdout.write(self.style.WARNING('📋 Credenciales admin: doc=0000000000 / pass=Admin2026*'))
        self.stdout.write(self.style.WARNING('🌐 Accede en: http://127.0.0.1:8000/'))

    def _crear_roles(self):
        from apps.usuarios.models import Rol
        for nombre in ['ADMINISTRADOR', 'INSTRUCTOR', 'APRENDIZ', 'COORDINADOR']:
            obj, c = Rol.objects.get_or_create(descripcion=nombre)
            self.stdout.write(f'  {"✅" if c else "⏭ "} Rol: {nombre}')

    def _crear_sedes(self):
        from apps.core.models import Sede, Espacio
        sedes = [
            {'nombre_sede': 'SEDE SALITRE', 'telefono_sede': '7366060', 'direccion_sede': 'CRA 57 C # 64 29'},
            {'nombre_sede': 'SEDE CSF',     'telefono_sede': '5461600', 'direccion_sede': 'CRA 13 # 65 10'},
        ]
        espacios_map = {
            'SEDE SALITRE': ['Sala Bienestar Principal', 'Consultorio Psicología 1', 'Consultorio Psicología 2'],
            'SEDE CSF':     ['Sala Bienestar CSF', 'Consultorio Orientación'],
        }
        for s in sedes:
            sede, c = Sede.objects.get_or_create(nombre_sede=s['nombre_sede'], defaults=s)
            self.stdout.write(f'  {"✅" if c else "⏭ "} Sede: {s["nombre_sede"]}')
            for nombre_esp in espacios_map[s['nombre_sede']]:
                _, ec = Espacio.objects.get_or_create(sede=sede, nombre_del_espacio=nombre_esp, defaults={'capacidad': 10})
                self.stdout.write(f'       {"✅" if ec else "⏭ "} Espacio: {nombre_esp}')

    def _crear_programas_fichas(self):
        from apps.core.models import Programa, Ficha
        programas = [
            (1, 'Tecnólogo en Análisis y Desarrollo de Software', 'Diseño y desarrollo de sistemas de información.'),
            (2, 'Técnico en Sistemas', 'Instalación y soporte técnico de software y hardware.'),
            (3, 'Gestión de Redes de Datos', 'Configuración y mantenimiento de infraestructuras de red.'),
            (4, 'Multimedia y Diseño Web', 'Creación de contenido digital y sitios web interactivos.'),
            (5, 'Programación de Software', 'Desarrollo de aplicaciones de escritorio y móviles.'),
            (6, 'Seguridad Informática', 'Protección de activos de información y defensa ante ataques.'),
        ]
        fichas = [
            (3065830, 'Tecnología en Análisis y Desarrollo de Software', 'DIURNA', 1),
            (3080485, 'Técnico en Sistemas', 'MANANA', 2),
            (2825640, 'Gestión de Redes de Datos', 'NOCTURNA', 3),
            (2901235, 'Multimedia y Diseño Web', 'MIXTA', 4),
            (3104567, 'Programación de Software', 'TARDE', 5),
            (2758901, 'Seguridad Informática', 'DIURNA', 6),
        ]
        prog_objs = {}
        for pid, nombre, desc in programas:
            obj, c = Programa.objects.get_or_create(id=pid, defaults={'nombre_programa': nombre, 'descripcion': desc})
            prog_objs[pid] = obj
            self.stdout.write(f'  {"✅" if c else "⏭ "} Programa: {nombre[:50]}')
        for fid, desc, jornada, pid in fichas:
            _, c = Ficha.objects.get_or_create(id_ficha=fid, defaults={'descripcion': desc, 'jornada_ficha': jornada, 'programa': prog_objs[pid]})
            self.stdout.write(f'  {"✅" if c else "⏭ "} Ficha: {fid}')

    def _crear_categorias_elementos(self):
        from apps.elementos.models import CategoriaElemento, Elemento
        cats = ['Equipos de Cómputo', 'Material Didáctico', 'Equipos Audiovisuales', 'Mobiliario']
        elementos = [
            ('Portátil Lenovo ThinkPad', 'Equipos de Cómputo', 'DISPONIBLE', 'BM-PC-001'),
            ('Tablet Samsung A8',        'Equipos de Cómputo', 'DISPONIBLE', 'BM-PC-002'),
            ('Kit Relajación Mindfulness','Material Didáctico','DISPONIBLE', 'BM-MD-001'),
            ('Proyector EPSON X49',      'Equipos Audiovisuales','DISPONIBLE','BM-AV-001'),
            ('Parlante Bluetooth JBL',   'Equipos Audiovisuales','DISPONIBLE','BM-AV-002'),
        ]
        cat_objs = {}
        for c in cats:
            obj, cr = CategoriaElemento.objects.get_or_create(descripcion=c)
            cat_objs[c] = obj
            self.stdout.write(f'  {"✅" if cr else "⏭ "} Categoría: {c}')
        for nombre, cat, estado, codigo in elementos:
            _, cr = Elemento.objects.get_or_create(codigo=codigo, defaults={'nombre_elemento': nombre, 'categoria': cat_objs[cat], 'estado_elemento': estado})
            self.stdout.write(f'  {"✅" if cr else "⏭ "} Elemento: {nombre}')

    def _crear_superusuario(self):
        from apps.usuarios.models import Usuario, Rol, UsuarioRol
        if not Usuario.objects.filter(documento='0000000000').exists():
            admin = Usuario.objects.create_user(
                documento='0000000000', password='Admin2026*',
                nombres='ADMINISTRADOR', apellidos='BIENESTARMIND',
                correo='admin@bienestarmind.sena.edu.co',
                genero='NO_ESPECIFICA',
                fecha_de_nacimiento=datetime.date(1990, 1, 1),
                is_staff=True, is_superuser=True,
            )
            rol_admin = Rol.objects.get(descripcion='ADMINISTRADOR')
            UsuarioRol.objects.create(usuario=admin, rol=rol_admin)
            self.stdout.write(self.style.SUCCESS('  ✅ Superusuario creado: doc=0000000000 / pass=Admin2026*'))
        else:
            self.stdout.write('  ⏭  Superusuario ya existe')
