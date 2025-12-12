from django.urls import path
from .views import (
    SubmitDataView,
    GetPerevalView,
    UpdatePerevalView,
    GetPerevalsByEmailView
)

urlpatterns = [
    path('submitData/', SubmitDataView.as_view(), name='submit-data'),
    path('submitData/<int:pk>/', GetPerevalView.as_view(), name='get-pereval'),
    path('submitData/<int:pk>/update/', UpdatePerevalView.as_view(), name='update-pereval'),
    path('submitData/by-email/', GetPerevalsByEmailView.as_view(), name='get-perevals-by-email'),
]