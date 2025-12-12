from rest_framework import serializers
from datetime import datetime
import base64
import uuid
from django.core.files.base import ContentFile
from .models import User, Coords, Level, Pereval, Image


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[])

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


class Base64ImageField(serializers.ImageField):
    """
    Поле для декодирования base64 в файл изображения
    """

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            # Формат: data:image/jpeg;base64,<данные>
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]

                # Проверяем расширение
                if ext not in ['jpeg', 'jpg', 'png', 'gif', 'bmp']:
                    raise serializers.ValidationError(f"Неподдерживаемый формат изображения: {ext}")

                # Декодируем base64
                decoded_file = base64.b64decode(imgstr)

                # Генерируем уникальное имя файла
                file_name = f"{uuid.uuid4().hex[:10]}.{ext}"
                data = ContentFile(decoded_file, name=file_name)

            except ValueError as e:
                raise serializers.ValidationError(f"Неверный формат base64: {str(e)}")
            except Exception as e:
                raise serializers.ValidationError(f"Ошибка обработки изображения: {str(e)}")

        return super().to_internal_value(data)


class ImageSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)

    class Meta:
        model = Image
        fields = ['image', 'title']
        extra_kwargs = {
            'title': {'required': True}
        }


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

        # Проверяем, что не больше 10 изображений
        if len(data['images']) > 10:
            raise serializers.ValidationError("Максимальное количество изображений - 10")

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

        # Проверяем количество изображений при обновлении
        if 'images' in data and len(data['images']) > 10:
            raise serializers.ValidationError("Максимальное количество изображений - 10")

        # Проверяем, чтобы не было полей пользователя
        if any(field in data for field in ['email', 'fam', 'name', 'otc', 'phone']):
            raise serializers.ValidationError("Изменение данных пользователя запрещено")
        return data