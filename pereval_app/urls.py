from django.urls import path
from .views import (
    SubmitDataView,
    PerevalDetailView
)

urlpatterns = [
    path('submitData/', SubmitDataView.as_view(), name='submit-data-list'),
    path('submitData/<int:id>/', PerevalDetailView.as_view(), name='submit-data-detail'),
]