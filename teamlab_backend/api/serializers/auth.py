from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import (
    validate_password as django_validate_password,
)
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer
)
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from projects.models import Specialization


User = get_user_model()


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user

        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError(
                {'current_password': 'Неверный пароль'}
            )
        
        return attrs
    
    def validate_new_password(self, value):
        user = self.context['request'].user

        try:
            django_validate_password(value, user)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages)
        
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    specialization_id = serializers.PrimaryKeyRelatedField(
        source='specialization',
        queryset=Specialization.objects.all(),
        required=False,
        allow_null=True,
    )
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'account_type',
            'specialization_id'
        )
        read_only_fields = ('id',)
        extra_kwargs = {
            'username': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
            'account_type': {'required': True, 'allow_blank': False},
        }
    
    def validate_password(self, value):
        try:
            django_validate_password(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages)
        
        return value

    def validate(self, attrs):
        account_type = attrs.get('account_type')
        specialization = attrs.get('specialization')

        if (
            account_type == User.AccountType.PARTICIPANT
            and specialization is None
        ):
            raise serializers.ValidationError({
                'specialization_id': (
                    'Для участника специализация обязательна.'
                )
            })

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


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
