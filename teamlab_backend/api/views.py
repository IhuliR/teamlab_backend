from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

from .serializers import TokenLoginSerializer, TokenRefreshWithUserSerializer
from projects.services import validate_project_role_can_be_deleted
from projects.models import (
    ProjectRole
)


class ProjectRoleViewSet(viewsets.ModelViewSet):
    queryset = ProjectRole.objects.all()

    def destroy(self, request, *args, **kwargs):
        role = self.get_object()

        validate_project_role_can_be_deleted(role)
        role.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class TokenLoginView(TokenObtainPairView):
    serializer_class = TokenLoginSerializer

class TokenRefreshWithUserView(TokenRefreshView):
    serializer_class = TokenRefreshWithUserSerializer

