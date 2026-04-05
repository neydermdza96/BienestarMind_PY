# BienestarMind — SENA CSF
Sistema de Gestión de Bienestar al Aprendiz · Centro de Servicios Financieros

## Puesta en marcha (primera vez)

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Copiar y configurar .env
copy .env.example .env          # Windows
cp .env.example .env            # Mac/Linux
# → Editar .env y poner DB_PASSWORD real

# 4. Verificar que todo esté listo
python verificar_entorno.py

# 5. Crear migraciones y aplicarlas
python manage.py makemigrations usuarios core asesorias elementos reservas reportes pqrs
python manage.py migrate

# 6. Cargar datos iniciales (sedes, programas, fichas, admin)
python manage.py poblar_datos

# 7. Correr el servidor
python manage.py runserver 0.0.0.0:8000
```

## Credenciales iniciales
- Documento: `0000000000`
- Contraseña: `Admin2026*`

## Accesos principales
- `/inicio/`         → Landing pública (antes del login)
- `/`                → Redirige a /inicio/
- `/usuarios/login/` → Login del sistema
- `/usuarios/registro/` → Registro de nuevos aprendices
- `/pqrs/`           → Centro de soporte PQRS (público)

## Módulos del sistema
- Dashboard con 4 gráficas métricas (Chart.js)
- Asesorías con notificaciones Email/SMS/WhatsApp
- Reservas de espacios y elementos
- Inventario completo con movimientos y alertas de stock
- PQRS (Peticiones, Quejas, Reclamos, Sugerencias, Felicitaciones)
- Calendario visual (FullCalendar 6)
- Horarios de instructores
- Notificaciones in-app con campanita en topbar
- Paneles específicos por rol (Instructor / Coordinador)
- Reportes PDF y Excel con paleta SENA

## Configuración de email (Gmail)
En el .env configurar:
```
EMAIL_HOST_USER=tu_correo@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx   # App Password de Google
```

## Stack tecnológico
- Python 3.10+ / Django 4.2
- PostgreSQL 15+
- Bootstrap 5 + Bootstrap Icons
- FullCalendar 6.1.9
- Chart.js 4.4.0
- ReportLab (PDF) + openpyxl (Excel)
- Twilio (SMS/WhatsApp)

## Equipo de Desarrollo
Proyecto desarrollado con compromiso por aprendices ADSO:

SCRUM # 2
Neyder Mendoza
Astrid Alvarez
Tatiana Bautista
Samuel Cardenas

© 2026 — BienestarMind. Innovación para la comunidad SENA.
