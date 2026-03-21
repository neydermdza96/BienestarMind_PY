"""URLs de reservas"""
from django.urls import path
from apps.reservas import views
app_name = 'reservas'
urlpatterns = [
    path('espacios/', views.lista_espacios, name='espacios'),
    path('espacios/crear/', views.crear_reserva_espacio, name='espacios_crear'),
    path('espacios/<int:pk>/cancelar/', views.eliminar_reserva_espacio, name='espacios_cancelar'),
    path('elementos/', views.lista_elementos, name='elementos'),
    path('elementos/crear/', views.crear_reserva_elemento, name='elementos_crear'),
]
