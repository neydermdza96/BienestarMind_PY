"""URLs de usuarios — BienestarMind"""
from django.urls import path
from apps.usuarios import views
app_name = 'usuarios'
urlpatterns = [
    # Autenticación
    path('login/',    views.login_view,   name='login'),
    path('logout/',   views.logout_view,  name='logout'),
    # Registro público
    path('registro/', views.registro_view, name='registro'),
    # Recuperación de contraseña
    path('recuperar/',                          views.recuperar_password,    name='recuperar_password'),
    path('recuperar/enviado/',                  views.recuperar_enviado,     name='recuperar_enviado'),
    path('recuperar/<str:token>/',              views.nueva_password,        name='nueva_password'),
    path('recuperar/<str:token>/confirmado/',   views.password_confirmado,   name='password_confirmado'),
    # Gestión de usuarios (admin)
    path('',                views.lista_usuarios,  name='lista'),
    path('crear/',          views.crear_usuario,   name='crear'),
    path('<int:pk>/editar/', views.editar_usuario,  name='editar'),
    path('<int:pk>/toggle/', views.toggle_usuario,  name='toggle'),
]
