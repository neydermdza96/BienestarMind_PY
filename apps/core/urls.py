"""URLs core — BienestarMind"""
from django.urls import path
from apps.core import views
app_name = 'core'
urlpatterns = [
    # Landing pública
    path('inicio/', views.landing, name='landing'),
    # Dashboard con métricas gráficas
    path('', views.dashboard, name='dashboard'),
    # Fichas
    path('fichas/',                      views.fichas,          name='fichas'),
    path('fichas/crear/',                views.crear_ficha,     name='fichas_crear'),
    path('fichas/<int:pk>/editar/',      views.editar_ficha,    name='fichas_editar'),
    path('fichas/<int:pk>/eliminar/',    views.eliminar_ficha,  name='fichas_eliminar'),
    # Programas
    path('programas/',                   views.programas,       name='programas'),
    path('programas/crear/',             views.crear_programa,  name='programas_crear'),
    path('programas/<int:pk>/editar/',   views.editar_programa, name='programas_editar'),
    # Sedes
    path('sedes/',                       views.sedes,           name='sedes'),
    path('sedes/crear/',                 views.crear_sede,      name='sedes_crear'),
    path('sedes/<int:pk>/editar/',       views.editar_sede,     name='sedes_editar'),
    # Espacios
    path('espacios/crear/',              views.crear_espacio,   name='espacios_crear'),
    path('espacios/<int:pk>/editar/',    views.editar_espacio,  name='espacios_editar'),
    path('espacios/<int:pk>/eliminar/',  views.eliminar_espacio,name='espacios_eliminar'),
    # Paneles de rol
    path('panel/instructor/',    views.panel_instructor,   name='panel_instructor'),
    path('panel/coordinador/',   views.panel_coordinador,  name='panel_coordinador'),
    # ── NUEVO: Calendario de reservas ─────────────────────────────
    path('calendario/',          views.calendario,         name='calendario'),
    path('calendario/api/',      views.calendario_api,     name='calendario_api'),
    # ── NUEVO: Horarios de instructores ───────────────────────────
    path('horarios/',                        views.horarios,          name='horarios'),
    path('horarios/crear/',                  views.crear_horario,     name='horarios_crear'),
    path('horarios/<int:pk>/eliminar/',      views.eliminar_horario,  name='horarios_eliminar'),
    path('horarios/api/',                    views.horarios_api,      name='horarios_api'),
    # ── NUEVO: Notificaciones in-app ──────────────────────────────
    path('notificaciones/',                  views.notificaciones,    name='notificaciones'),
    path('notificaciones/leer/<int:pk>/',    views.leer_notificacion, name='notif_leer'),
    path('notificaciones/leer-todas/',       views.leer_todas,        name='notif_leer_todas'),
    path('notificaciones/api/conteo/',       views.notif_conteo_api,  name='notif_conteo'),
    # ── NUEVO: Dashboard métricas API ────────────────────────────
    path('metricas/api/',                    views.metricas_api,      name='metricas_api'),
]
