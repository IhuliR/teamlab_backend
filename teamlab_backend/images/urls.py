from django.urls import path

from .views import ImageUploadCreateView, ImageUploadConfirmView


urlpatterns = [
    path('', ImageUploadCreateView.as_view(), name='image-upload-create'),
    path(
        '<uuid:upload_id>/confirm/',
        ImageUploadConfirmView.as_view(),
        name='image-upload-confirm',
    )
]
