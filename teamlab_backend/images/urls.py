from django.urls import path

from .views import ImageUploadCreateView


urlpatterns = [
    path('', ImageUploadCreateView.as_view(), name='image-upload-create'),
]
