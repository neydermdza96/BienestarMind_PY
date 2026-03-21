"""URLs elementos e inventario"""
from django.urls import path
from apps.elementos import views
app_name = 'elementos'
urlpatterns = [
    # Elementos
    path('',                   views.lista_elementos,  name='lista'),
    path('crear/',             views.crear_elemento,   name='crear'),
    path('<int:pk>/editar/',   views.editar_elemento,  name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_elemento,name='eliminar'),
    # Categorías
    path('categorias/',        views.lista_categorias,  name='categorias'),
    path('categorias/crear/',  views.crear_categoria,   name='categorias_crear'),
    # Inventario
    path('inventario/',                    views.inventario_dashboard, name='inventario'),
    path('inventario/<int:pk>/entrada/',   views.registrar_entrada,    name='inventario_entrada'),
    path('inventario/<int:pk>/salida/',    views.registrar_salida,     name='inventario_salida'),
    path('inventario/<int:pk>/ajuste/',    views.ajustar_inventario,   name='inventario_ajuste'),
    path('inventario/<int:pk>/devolver/',  views.devolver_elemento,    name='inventario_devolver'),
    path('inventario/historial/',          views.historial_movimientos,name='inventario_historial'),
]
