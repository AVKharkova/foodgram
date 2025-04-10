from django.contrib.auth import get_user_model

from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
)

from api.serializers.users import UserProfileSerializer

User = get_user_model()


class CustomUserCreateSerializer(DjoserUserCreateSerializer):
    """Кастомный сериализатор для создания юзера через Djoser."""

    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name', 'password',
        )


class CustomUserSerializer(UserProfileSerializer):
    """Кастомный сериализатор для отображения юзера через Djoser."""

    class Meta(UserProfileSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name',
            'avatar', 'is_subscribed',
        )
