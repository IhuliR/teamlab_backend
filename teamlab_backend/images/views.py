from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ImageUploadCreateSerializer
from .services import create_image_upload, confirm_image_upload


class ImageUploadCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ImageUploadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        upload, presigned = create_image_upload(
            user=request.user,
            validated_data=serializer.validated_data,
        )

        return Response(
            {
                'upload_id': str(upload.id),
                'status': upload.status,
                'expires_at': upload.expires_at.isoformat(),
                'upload_url': presigned['url'],
                'upload_fields': presigned['fields'],
            },
            status=status.HTTP_201_CREATED,
        )


class ImageUploadConfirmView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, upload_id):
        upload = confirm_image_upload(
            user=request.user,
            upload_id=upload_id,
        )
        return Response({
            'upload_id': str(upload.id),
            'status': upload.status,
        })
