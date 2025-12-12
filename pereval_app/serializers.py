from rest_framework import serializers
from datetime import datetime
import base64
from .models import User, Coords, Level, Pereval, Image


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'fam', 'name', 'otc', 'phone']
        read_only_fields = ['email', 'fam', 'name', 'otc', 'phone']  # Запрещаем редактирование

    def validate_email(self, value):
        """Проверка уникальности email"""
        if User.objects.filter(email=value).exists():
            pass
        return value


class CoordsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coords
        fields = ['latitude', 'longitude', 'height']


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ['winter', 'summer', 'autumn', 'spring']


class ImageSerializer(serializers.Serializer):
    data = serializers.CharField(required=True)
    title = serializers.CharField(required=True, max_length=255)

    def validate_data(self, value):
        """Проверка формата изображения"""
        if isinstance(value, str) and value.startswith('data:image'):
            try:
                # Проверяем, что это валидный base64
                base64.b64decode(value.split(',')[1])
                return value
            except:
                raise serializers.ValidationError("Invalid base64 image data")
        # Принимаем обычный base64 без префикса
        try:
            base64.b64decode(value)
            return value
        except:
            raise serializers.ValidationError("Invalid base64 image data")


class PerevalSerializer(serializers.Serializer):
    beauty_title = serializers.CharField(required=True, max_length=255)
    title = serializers.CharField(required=True, max_length=255)
    other_titles = serializers.CharField(required=False, allow_blank=True, max_length=255)
    connect = serializers.CharField(required=False, allow_blank=True, max_length=255)
    add_time = serializers.DateTimeField(required=False, default=datetime.now)
    user = UserSerializer(required=True)
    coords = CoordsSerializer(required=True)
    level = LevelSerializer(required=True)
    images = ImageSerializer(many=True, required=True)

    def validate(self, data):
        """Упрощенная валидация - только обязательные поля"""
        if 'images' not in data or not data['images']:
            raise serializers.ValidationError("At least one image is required")
        return data


class PerevalUpdateSerializer(serializers.Serializer):
    """Сериализатор для обновления данных (без полей пользователя)"""
    beauty_title = serializers.CharField(required=False, max_length=255)
    title = serializers.CharField(required=False, max_length=255)
    other_titles = serializers.CharField(required=False, allow_blank=True, max_length=255)
    connect = serializers.CharField(required=False, allow_blank=True, max_length=255)
    coords = CoordsSerializer(required=False)
    level = LevelSerializer(required=False)
    images = ImageSerializer(many=True, required=False)

    def validate(self, data):
        """Проверяем, что есть хотя бы одно поле для обновления"""
        if not data:
            raise serializers.ValidationError("Нет данных для обновления")
        return data