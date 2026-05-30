from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

from .serializers import TokenLoginSerializer, TokenRefreshWithUserSerializer


class TokenLoginView(TokenObtainPairView):
    serializer_class = TokenLoginSerializer

class TokenRefreshWithUserView(TokenRefreshView):
    serializer_class = TokenRefreshWithUserSerializer

