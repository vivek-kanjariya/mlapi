from django.urls import path
from .views import PredictView, UploadMasterView, index, TestJSONView, SOPView
from .dispatch import DispatchPlannerView  # ✅ import it

urlpatterns = [
    path('', index, name='home'),
    path('predict/', PredictView.as_view(), name='predict'),
    path('sop/', SOPView.as_view(), name='sop'),
    path('upload-master/', UploadMasterView.as_view(), name='upload_master'),
    path('data/', TestJSONView.as_view(), name='data_handler'),
    
    # ✅ Your NEW Dispatch route
    path('dispatch/', DispatchPlannerView.as_view(), name='dispatch_planner'),
]
