from django.urls import path

from .views import (
    ImageUploadAttachView,
    ImageUploadCreateView,
    ImageUploadConfirmView,
    ImageUploadDetailView,
)


urlpatterns = [
    path('', ImageUploadCreateView.as_view(), name='image-upload-create'),
    path(
        '<uuid:upload_id>/confirm/',
        ImageUploadConfirmView.as_view(),
        name='image-upload-confirm',
    ),
    path(
        '<uuid:upload_id>/',
        ImageUploadDetailView.as_view(),
        name='image-upload-detail',
    ),
    path(
        '<uuid:upload_id>/attach/',
        ImageUploadAttachView.as_view(),
        name='image-upload-attach',
    ),
]
