from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer
)
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


class AuthUserSerializer(serializers.ModelSerializer):
    """Краткие данные пользователя для auth-ответов."""

    class Meta:
        model = User
        fields = ('id', 'username', 'account_type')
        read_only_fields = fields


class TokenLoginSerializer(TokenObtainPairSerializer):
    """JWT-login по username/password с информацией о user в ответе."""

    def validate(self, attrs):
        data = super().validate(attrs)

        data['user'] = AuthUserSerializer(self.user).data
        return data


class TokenRefreshWithUserSerializer(TokenRefreshSerializer):
    """Refresh access-токена с информацией о user в ответе."""

    def validate(self, attrs):
        data = super().validate(attrs)

        try:
            refresh = RefreshToken(attrs['refresh'])
        except TokenError as error:
            raise InvalidToken(error.args[0])
        
        user_id = refresh[api_settings.USER_ID_CLAIM]
        user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        data['user'] = AuthUserSerializer(user).data
        return data
