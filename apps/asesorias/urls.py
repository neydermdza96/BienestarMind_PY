"""URLs de asesorías"""
from django.urls import path
from apps.asesorias import views
app_name = 'asesorias'
urlpatterns = [
    path('', views.lista_asesorias, name='lista'),
    path('crear/', views.crear_asesoria, name='crear'),
    path('<int:pk>/editar/', views.editar_asesoria, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_asesoria, name='eliminar'),
]
