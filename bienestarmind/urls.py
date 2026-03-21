from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('usuarios/', include('apps.usuarios.urls')),
    path('asesorias/', include('apps.asesorias.urls')),
    path('reservas/', include('apps.reservas.urls')),
    path('elementos/', include('apps.elementos.urls')),
    path('reportes/', include('apps.reportes.urls')),
    path('pqrs/', include('apps.pqrs.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)