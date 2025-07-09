import os
from django.core.wsgi import get_wsgi_application

# ✅ Set the correct settings module (important)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mlserver.settings')

application = get_wsgi_application()
