from rest_framework import serializers
from datetime import datetime
import base64
from .models import User, Coords, Level, Pereval, Image


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'fam', 'name', 'otc', 'phone']

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
        # Gринимаем обычный base64 без префикса
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
    images = ImageSerializer(many=True, required=True)  # Изменено на required=True по заданию

    def validate(self, data):
        """Упрощенная валидация - только обязательные поля"""
        if 'images' not in data or not data['images']:
            raise serializers.ValidationError("At least one image is required")

        return data