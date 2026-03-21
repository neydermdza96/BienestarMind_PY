import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bienestarmind.settings')
application = get_wsgi_application()
