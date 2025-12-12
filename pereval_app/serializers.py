from rest_framework import serializers
from datetime import datetime
import base64
from .models import User, Coords, Level, Pereval, Image


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[])  # Убираем стандартные валидаторы

    class Meta:
        model = User
        fields = ['email', 'fam', 'name', 'otc', 'phone']
        extra_kwargs = {
            'email': {'validators': []},
            'fam': {'validators': []},
            'name': {'validators': []},
            'otc': {'validators': []},
            'phone': {'validators': []},
        }

    def validate(self, data):
        """Валидация пользователя - только обязательные поля"""
        # Обязательные поля
        required_fields = ['email', 'fam', 'name', 'phone']
        for field in required_fields:
            if field not in data or not data[field]:
                raise serializers.ValidationError(
                    f"Поле '{field}' обязательно для пользователя"
                )
        return data

    def create(self, validated_data):
        """Создание или получение пользователя"""
        user, created = User.objects.get_or_create(
            email=validated_data['email'],
            defaults={
                'fam': validated_data.get('fam', ''),
                'name': validated_data.get('name', ''),
                'otc': validated_data.get('otc', ''),
                'phone': validated_data.get('phone', '')
            }
        )
        return user

    def update(self, instance, validated_data):
        """Обновление - только при создании, при обновлении не вызывается"""
        raise serializers.ValidationError("Обновление данных пользователя запрещено")


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

    def __init__(self, *args, **kwargs):
        """Передаем контекст в UserSerializer"""
        super().__init__(*args, **kwargs)
        if 'user' in self.fields:
            self.fields['user'].context['is_create'] = True

    def validate(self, data):
        """Общая валидация"""
        if 'images' not in data or not data['images']:
            raise serializers.ValidationError("Необходимо хотя бы одно изображение")
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
        # Проверяем, чтобы не было полей пользователя
        if any(field in data for field in ['email', 'fam', 'name', 'otc', 'phone']):
            raise serializers.ValidationError("Изменение данных пользователя запрещено")
        return data