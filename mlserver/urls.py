from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('healthz/', lambda req: JsonResponse({"status": "OK"})),
]
