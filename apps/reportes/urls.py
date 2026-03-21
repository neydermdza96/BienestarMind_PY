"""URLs de reportes"""
from django.urls import path
from apps.reportes import views
app_name = 'reportes'
urlpatterns = [
    path('', views.index, name='index'),
    path('asesorias/pdf/', views.reporte_asesorias_pdf, name='asesorias_pdf'),
    path('asesorias/excel/', views.reporte_asesorias_excel, name='asesorias_excel'),
    path('reservas-espacios/pdf/', views.reporte_reservas_espacios_pdf, name='res_espacios_pdf'),
    path('reservas-espacios/excel/', views.reporte_reservas_espacios_excel, name='res_espacios_excel'),
    path('usuarios/pdf/', views.reporte_usuarios_pdf, name='usuarios_pdf'),
    path('usuarios/excel/', views.reporte_usuarios_excel, name='usuarios_excel'),
]
