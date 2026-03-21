from django.urls import path
from apps.pqrs import views
app_name = 'pqrs'
urlpatterns = [
    path('',              views.crear_pqrs,    name='crear'),
    path('enviado/',      views.enviado,        name='enviado'),
    path('mis-pqrs/',     views.mis_pqrs,       name='mis_pqrs'),
    path('admin/',        views.lista_admin,    name='admin'),
    path('admin/<int:pk>/responder/', views.responder_pqrs, name='responder'),
    path('admin/<int:pk>/detalle/',   views.detalle_pqrs,   name='detalle'),
]
