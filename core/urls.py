from django.urls import path
from .views import PredictView, UploadMasterView
from .views import index, TestJSONView
from core.views import index  # ✅ import index view
from core.views import SOPView  # ✅ import view

urlpatterns = [
    path('', index, name='home'),  # ✅ serve / → index.html
    path('predict/', PredictView.as_view(), name='predict'),
    path('sop/', SOPView.as_view(), name='sop'),
    path('upload-master/', UploadMasterView.as_view(), name='upload_master'),
    path('data/', TestJSONView.as_view(), name='data_handler'),  # ✅ single endpoint
]
