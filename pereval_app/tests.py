import os
import json
import base64
from io import BytesIO
from PIL import Image
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from .models import User, Coords, Level, Pereval, Image
from .serializers import PerevalSerializer, PerevalUpdateSerializer, UserSerializer
import tempfile
from django.conf import settings


# Тесты для моделей
class ModelTests(TestCase):
    """Тесты для моделей базы данных"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.user = User.objects.create(
            email="test@example.com",
            fam="Иванов",
            name="Иван",
            otc="Иванович",
            phone="+79991234567"
        )

        self.coords = Coords.objects.create(
            latitude=55.755826,
            longitude=37.617300,
            height=150
        )

        self.level = Level.objects.create(
            winter="1A",
            summer="1Б",
            autumn="1А",
            spring="1Б"
        )

        self.pereval = Pereval.objects.create(
            beauty_title="Перевал красивый",
            title="Главный перевал",
            other_titles="Дополнительные названия",
            connect="Соединяет долины",
            user=self.user,
            coords=self.coords,
            level=self.level
        )

    def test_user_creation(self):
        """Тест создания пользователя"""
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.fam, "Иванов")
        self.assertEqual(self.user.name, "Иван")
        self.assertEqual(self.user.phone, "+79991234567")
        self.assertEqual(str(self.user), "Иванов Иван (test@example.com)")

    def test_coords_creation(self):
        """Тест создания координат"""
        self.assertEqual(float(self.coords.latitude), 55.755826)
        self.assertEqual(float(self.coords.longitude), 37.617300)
        self.assertEqual(self.coords.height, 150)
        self.assertEqual(str(self.coords), "(55.755826, 37.617300, 150)")

    def test_level_creation(self):
        """Тест создания уровня сложности"""
        self.assertEqual(self.level.winter, "1A")
        self.assertEqual(self.level.summer, "1Б")
        self.assertEqual(str(self.level), "зима: 1A, лето: 1Б, осень: 1А, весна: 1Б")

    def test_pereval_creation(self):
        """Тест создания перевала"""
        self.assertEqual(self.pereval.beauty_title, "Перевал красивый")
        self.assertEqual(self.pereval.title, "Главный перевал")
        self.assertEqual(self.pereval.status, 'new')
        self.assertTrue(self.pereval.can_be_edited())
        self.assertEqual(str(self.pereval), "Главный перевал (Перевал красивый) - Новый")

    def test_pereval_can_be_edited(self):
        """Тест проверки возможности редактирования"""
        # Новый перевал можно редактировать
        self.assertTrue(self.pereval.can_be_edited())

        # Перевал с другими статусами нельзя редактировать
        self.pereval.status = 'pending'
        self.assertFalse(self.pereval.can_be_edited())

        self.pereval.status = 'accepted'
        self.assertFalse(self.pereval.can_be_edited())

        self.pereval.status = 'rejected'
        self.assertFalse(self.pereval.can_be_edited())

    def test_image_creation(self):
        """Тест создания изображения"""
        # Создаем тестовое изображение
        image = Image.new('RGB', (100, 100), color='red')
        image_file = BytesIO()
        image.save(image_file, 'JPEG')
        image_file.seek(0)

        test_image = SimpleUploadedFile(
            "test_image.jpg",
            image_file.read(),
            content_type="image/jpeg"
        )

        image_obj = Image.objects.create(
            pereval=self.pereval,
            image=test_image,
            title="Тестовое изображение"
        )

        self.assertEqual(image_obj.title, "Тестовое изображение")
        self.assertEqual(image_obj.pereval, self.pereval)
        self.assertTrue(image_obj.image.name.startswith('pereval_images/'))


# Тесты для сериализаторов
class SerializerTests(TestCase):
    """Тесты для сериализаторов"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.valid_pereval_data = {
            "beauty_title": "Красивый перевал",
            "title": "Основной перевал",
            "other_titles": "Другие названия",
            "connect": "Соединяет вершины",
            "user": {
                "email": "test@example.com",
                "fam": "Петров",
                "name": "Петр",
                "otc": "Петрович",
                "phone": "+79998887766"
            },
            "coords": {
                "latitude": 56.8346,
                "longitude": 60.6123,
                "height": 350
            },
            "level": {
                "winter": "2A",
                "summer": "2Б",
                "autumn": "2А",
                "spring": "2Б"
            },
            "images": [
                {
                    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
                    "title": "Тестовое изображение"
                }
            ]
        }

        self.invalid_pereval_data = {
            "beauty_title": "",
            "title": "",
            "user": {
                "email": "invalid-email",
                "fam": "",
                "name": "",
                "phone": ""
            },
            "coords": {
                "latitude": 200,  # Неверная широта
                "longitude": 400,  # Неверная долгота
                "height": -100  # Неверная высота
            },
            "level": {},
            "images": []
        }

    def test_pereval_serializer_valid(self):
        """Тест валидации корректных данных"""
        serializer = PerevalSerializer(data=self.valid_pereval_data)
        self.assertTrue(serializer.is_valid())

    def test_pereval_serializer_invalid(self):
        """Тест валидации некорректных данных"""
        serializer = PerevalSerializer(data=self.invalid_pereval_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('beauty_title', serializer.errors)
        self.assertIn('title', serializer.errors)
        self.assertIn('images', serializer.errors)

    def test_user_serializer_create(self):
        """Тест создания пользователя через сериализатор"""
        user_data = {
            "email": "new@example.com",
            "fam": "Сидоров",
            "name": "Сидор",
            "otc": "Сидорович",
            "phone": "+79997776655"
        }

        serializer = UserSerializer(data=user_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.fam, "Сидоров")

        # Проверяем, что пользователь создан в БД
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

    def test_user_serializer_get_or_create(self):
        """Тест получения существующего пользователя"""
        # Создаем пользователя
        User.objects.create(
            email="existing@example.com",
            fam="Существующий",
            name="Пользователь",
            phone="+79994443322"
        )

        # Пытаемся создать того же пользователя
        user_data = {
            "email": "existing@example.com",
            "fam": "НоваяФамилия",  # Эти данные не должны обновиться
            "name": "НовоеИмя",
            "phone": "+79991112233"
        }

        serializer = UserSerializer(data=user_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        # Проверяем, что пользователь не создан заново
        self.assertEqual(User.objects.filter(email="existing@example.com").count(), 1)
        # Проверяем, что данные не обновились
        self.assertEqual(user.fam, "Существующий")  # Осталась старая фамилия

    def test_pereval_update_serializer(self):
        """Тест сериализатора для обновления"""
        update_data = {
            "beauty_title": "Обновленный перевал",
            "coords": {
                "latitude": 57.1234,
                "longitude": 61.4321,
                "height": 400
            }
        }

        serializer = PerevalUpdateSerializer(data=update_data)
        self.assertTrue(serializer.is_valid())

    def test_pereval_update_serializer_no_data(self):
        """Тест сериализатора обновления без данных"""
        serializer = PerevalUpdateSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)


# Тесты для API endpoints
class APITests(APITestCase):
    """Тесты для REST API endpoints"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.client = APIClient()

        # Создаем тестовых пользователей
        self.user1 = User.objects.create(
            email="user1@example.com",
            fam="Иванов",
            name="Иван",
            otc="Иванович",
            phone="+79991234567"
        )

        self.user2 = User.objects.create(
            email="user2@example.com",
            fam="Петров",
            name="Петр",
            otc="Петрович",
            phone="+79998887766"
        )

        # Создаем координаты
        self.coords1 = Coords.objects.create(
            latitude=55.755826,
            longitude=37.617300,
            height=150
        )

        self.coords2 = Coords.objects.create(
            latitude=56.8346,
            longitude=60.6123,
            height=350
        )

        # Создаем уровни сложности
        self.level1 = Level.objects.create(
            winter="1A",
            summer="1Б",
            autumn="1А",
            spring="1Б"
        )

        self.level2 = Level.objects.create(
            winter="2A",
            summer="2Б",
            autumn="2А",
            spring="2Б"
        )

        # Создаем перевалы
        self.pereval1 = Pereval.objects.create(
            beauty_title="Первый перевал",
            title="Перевал №1",
            other_titles="Дополнительные названия 1",
            connect="Соединяет долину А и Б",
            user=self.user1,
            coords=self.coords1,
            level=self.level1
        )

        self.pereval2 = Pereval.objects.create(
            beauty_title="Второй перевал",
            title="Перевал №2",
            other_titles="Дополнительные названия 2",
            connect="Соединяет долину В и Г",
            user=self.user1,
            coords=self.coords2,
            level=self.level2
        )

        # Создаем перевал для второго пользователя
        self.pereval3 = Pereval.objects.create(
            beauty_title="Третий перевал",
            title="Перевал №3",
            other_titles="Дополнительные названия 3",
            connect="Соединяет долину Д и Е",
            user=self.user2,
            coords=self.coords1,
            level=self.level1
        )

        # URL для тестирования
        self.submit_data_url = reverse('submit-data-list')
        self.submit_data_detail_url = lambda id: reverse('submit-data-detail', args=[id])

        # Тестовые данные для создания перевала
        self.create_pereval_data = {
            "beauty_title": "Тестовый перевал API",
            "title": "API Перевал",
            "other_titles": "Тестовые другие названия",
            "connect": "Тестовое соединение",
            "user": {
                "email": "api_test@example.com",
                "fam": "API",
                "name": "Тест",
                "otc": "Тестович",
                "phone": "+79995554433"
            },
            "coords": {
                "latitude": 58.123456,
                "longitude": 62.654321,
                "height": 500
            },
            "level": {
                "winter": "3A",
                "summer": "3Б",
                "autumn": "3А",
                "spring": "3Б"
            },
            "images": [
                {
                    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
                    "title": "API тестовое изображение"
                }
            ]
        }

    def generate_test_image_base64(self):
        """Генерация тестового изображения в формате base64"""
        # Создаем простое изображение
        image = Image.new('RGB', (100, 100), color='blue')

        # Сохраняем в BytesIO
        buffer = BytesIO()
        image.save(buffer, format='JPEG')
        buffer.seek(0)

        # Кодируем в base64
        encoded_string = base64.b64encode(buffer.read()).decode('utf-8')
        return f"data:image/jpeg;base64,{encoded_string}"

    # Тесты для GET запросов

    def test_get_perevals_by_email_success(self):
        """Тест получения перевалов по email пользователя"""
        response = self.client.get(
            self.submit_data_url,
            {'user__email': 'user1@example.com'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 200)
        self.assertEqual(response.data['message'], 'Найдено 2 перевалов')
        self.assertEqual(len(response.data['data']), 2)

    def test_get_perevals_by_email_no_email(self):
        """Тест получения перевалов без указания email"""
        response = self.client.get(self.submit_data_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 400)
        self.assertEqual(response.data['message'], 'Не указан email пользователя')

    def test_get_perevals_by_email_not_found(self):
        """Тест получения перевалов для несуществующего email"""
        response = self.client.get(
            self.submit_data_url,
            {'user__email': 'nonexistent@example.com'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 200)
        self.assertEqual(
            response.data['message'],
            'Для пользователя с email nonexistent@example.com перевалы не найдены'
        )
        self.assertEqual(len(response.data['data']), 0)

    def test_get_pereval_by_id_success(self):
        """Тест получения перевала по ID"""
        response = self.client.get(self.submit_data_detail_url(self.pereval1.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 200)
        self.assertEqual(response.data['message'], 'Найдено')
        self.assertEqual(response.data['data']['id'], self.pereval1.id)
        self.assertEqual(response.data['data']['title'], 'Перевал №1')
        self.assertEqual(response.data['data']['user']['email'], 'user1@example.com')

    def test_get_pereval_by_id_not_found(self):
        """Тест получения несуществующего перевала"""
        response = self.client.get(self.submit_data_detail_url(99999))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['status'], 404)
        self.assertEqual(response.data['message'], 'Перевал с ID 99999 не найден')

    # Тесты для POST запросов

    def test_create_pereval_success(self):
        """Тест успешного создания перевала"""
        response = self.client.post(
            self.submit_data_url,
            data=json.dumps(self.create_pereval_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 200)
        self.assertEqual(response.data['message'], 'Отправлено успешно')
        self.assertIsNotNone(response.data['id'])

        # Проверяем, что перевал создан в БД
        pereval_id = response.data['id']
        self.assertTrue(Pereval.objects.filter(id=pereval_id).exists())

        # Проверяем данные созданного перевала
        pereval = Pereval.objects.get(id=pereval_id)
        self.assertEqual(pereval.title, 'API Перевал')
        self.assertEqual(pereval.user.email, 'api_test@example.com')
        self.assertEqual(pereval.images.count(), 1)

    def test_create_pereval_invalid_data(self):
        """Тест создания перевала с некорректными данными"""
        invalid_data = self.create_pereval_data.copy()
        invalid_data['user']['email'] = 'invalid-email'  # Невалидный email

        response = self.client.post(
            self.submit_data_url,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 400)
        self.assertIn('user', response.data['errors'])

    def test_create_pereval_no_images(self):
        """Тест создания перевала без изображений"""
        data_without_images = self.create_pereval_data.copy()
        data_without_images['images'] = []

        response = self.client.post(
            self.submit_data_url,
            data=json.dumps(data_without_images),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 400)
        self.assertIn('images', response.data['errors'])

    def test_create_pereval_too_many_images(self):
        """Тест создания перевала с более чем 10 изображениями"""
        data_many_images = self.create_pereval_data.copy()
        data_many_images['images'] = []

        # Создаем 11 изображений
        for i in range(11):
            data_many_images['images'].append({
                "image": self.generate_test_image_base64(),
                "title": f"Изображение {i + 1}"
            })

        response = self.client.post(
            self.submit_data_url,
            data=json.dumps(data_many_images),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 400)
        self.assertIn('images', response.data['errors'])

    # Тесты для PATCH запросов

    def test_update_pereval_success(self):
        """Тест успешного обновления перевала"""
        # Создаем новый перевал для обновления
        pereval = Pereval.objects.create(
            beauty_title="Перевал для обновления",
            title="Исходный перевал",
            other_titles="Исходные названия",
            connect="Исходное соединение",
            user=self.user1,
            coords=self.coords1,
            level=self.level1,
            status='new'  # Важно: только new можно редактировать
        )

        update_data = {
            "beauty_title": "Обновленный перевал",
            "title": "Обновленный заголовок",
            "coords": {
                "latitude": 59.876543,
                "longitude": 63.123456,
                "height": 600
            },
            "level": {
                "winter": "4A",
                "summer": "4Б",
                "autumn": "4А",
                "spring": "4Б"
            },
            "images": [
                {
                    "image": self.generate_test_image_base64(),
                    "title": "Обновленное изображение"
                }
            ]
        }

        response = self.client.patch(
            self.submit_data_detail_url(pereval.id),
            data=json.dumps(update_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['state'], 1)
        self.assertEqual(response.data['message'], 'Запись успешно обновлена')

        # Проверяем обновленные данные
        pereval.refresh_from_db()
        self.assertEqual(pereval.beauty_title, "Обновленный перевал")
        self.assertEqual(pereval.title, "Обновленный заголовок")
        self.assertEqual(float(pereval.coords.latitude), 59.876543)
        self.assertEqual(pereval.level.winter, "4A")
        self.assertEqual(pereval.images.count(), 1)

    def test_update_pereval_not_found(self):
        """Тест обновления несуществующего перевала"""
        update_data = {"title": "Новый заголовок"}

        response = self.client.patch(
            self.submit_data_detail_url(99999),
            data=json.dumps(update_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['state'], 0)
        self.assertEqual(response.data['message'], 'Перевал с ID 99999 не найден')

    def test_update_pereval_not_new_status(self):
        """Тест обновления перевала со статусом не 'new'"""
        pereval = Pereval.objects.create(
            beauty_title="Перевал не для обновления",
            title="Заблокированный перевал",
            user=self.user1,
            coords=self.coords1,
            level=self.level1,
            status='accepted'  # Нельзя редактировать
        )

        update_data = {"title": "Попытка обновления"}

        response = self.client.patch(
            self.submit_data_detail_url(pereval.id),
            data=json.dumps(update_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['state'], 0)
        self.assertIn('Редактирование запрещено', response.data['message'])

    def test_update_pereval_user_data_not_allowed(self):
        """Тест попытки обновления данных пользователя"""
        pereval = Pereval.objects.create(
            beauty_title="Перевал для теста пользователя",
            title="Тестовый перевал",
            user=self.user1,
            coords=self.coords1,
            level=self.level1,
            status='new'
        )

        # Пытаемся обновить данные пользователя напрямую
        update_data = {
            "title": "Новый заголовок",
            "user": {
                "email": "hacked@example.com"
            }
        }

        response = self.client.patch(
            self.submit_data_detail_url(pereval.id),
            data=json.dumps(update_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['state'], 0)
        self.assertIn('Изменение данных пользователя запрещено', response.data['message'])

        # Пытаемся обновить данные пользователя через поле email
        update_data = {
            "title": "Новый заголовок",
            "email": "hacked2@example.com"
        }

        response = self.client.patch(
            self.submit_data_detail_url(pereval.id),
            data=json.dumps(update_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['state'], 0)

    def test_update_pereval_partial(self):
        """Тест частичного обновления перевала"""
        pereval = Pereval.objects.create(
            beauty_title="Частичное обновление",
            title="Исходный",
            user=self.user1,
            coords=self.coords1,
            level=self.level1,
            status='new'
        )

        # Обновляем только одно поле
        update_data = {"title": "Частично обновленный"}

        response = self.client.patch(
            self.submit_data_detail_url(pereval.id),
            data=json.dumps(update_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['state'], 1)

        pereval.refresh_from_db()
        self.assertEqual(pereval.title, "Частично обновленный")
        self.assertEqual(pereval.beauty_title, "Частичное обновление")  # Не изменилось

    # Интеграционные тесты

    def test_integration_create_and_get(self):
        """Интеграционный тест: создание и получение перевала"""
        # 1. Создаем перевал
        create_response = self.client.post(
            self.submit_data_url,
            data=json.dumps(self.create_pereval_data),
            content_type='application/json'
        )

        self.assertEqual(create_response.status_code, status.HTTP_200_OK)
        pereval_id = create_response.data['id']

        # 2. Получаем созданный перевал по ID
        get_response = self.client.get(self.submit_data_detail_url(pereval_id))

        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data['data']['id'], pereval_id)
        self.assertEqual(get_response.data['data']['title'], 'API Перевал')
        self.assertEqual(get_response.data['data']['user']['email'], 'api_test@example.com')

    def test_integration_create_update_get(self):
        """Интеграционный тест: создание, обновление и получение перевала"""
        # 1. Создаем перевал
        create_data = self.create_pereval_data.copy()
        create_data['title'] = "Исходный заголовок"

        create_response = self.client.post(
            self.submit_data_url,
            data=json.dumps(create_data),
            content_type='application/json'
        )

        self.assertEqual(create_response.status_code, status.HTTP_200_OK)
        pereval_id = create_response.data['id']

        # 2. Обновляем перевал
        update_data = {
            "title": "Обновленный через PATCH",
            "coords": {
                "latitude": 60.000000,
                "longitude": 65.000000,
                "height": 1000
            }
        }

        update_response = self.client.patch(
            self.submit_data_detail_url(pereval_id),
            data=json.dumps(update_data),
            content_type='application/json'
        )

        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['state'], 1)

        # 3. Получаем обновленный перевал
        get_response = self.client.get(self.submit_data_detail_url(pereval_id))

        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data['data']['title'], 'Обновленный через PATCH')
        self.assertEqual(float(get_response.data['data']['coords']['latitude']), 60.000000)
        self.assertEqual(get_response.data['data']['coords']['height'], 1000)

    def test_integration_get_by_email_after_create(self):
        """Интеграционный тест: создание и поиск по email"""
        # 1. Создаем перевал для нового пользователя
        new_user_email = "integration@example.com"
        create_data = self.create_pereval_data.copy()
        create_data['user']['email'] = new_user_email

        create_response = self.client.post(
            self.submit_data_url,
            data=json.dumps(create_data),
            content_type='application/json'
        )

        self.assertEqual(create_response.status_code, status.HTTP_200_OK)

        # 2. Создаем еще один перевал для того же пользователя
        create_data2 = create_data.copy()
        create_data2['title'] = "Второй перевал интеграции"

        create_response2 = self.client.post(
            self.submit_data_url,
            data=json.dumps(create_data2),
            content_type='application/json'
        )

        self.assertEqual(create_response2.status_code, status.HTTP_200_OK)

        # 3. Ищем все перевалы по email
        search_response = self.client.get(
            self.submit_data_url,
            {'user__email': new_user_email}
        )

        self.assertEqual(search_response.status_code, status.HTTP_200_OK)
        self.assertEqual(search_response.data['status'], 200)
        self.assertEqual(search_response.data['message'], f'Найдено 2 перевалов')
        self.assertEqual(len(search_response.data['data']), 2)

        # Проверяем, что найдены оба перевала
        titles = [item['title'] for item in search_response.data['data']]
        self.assertIn('API Перевал', titles)
        self.assertIn('Второй перевал интеграции', titles)

    # Тесты граничных случаев

    def test_create_pereval_with_existing_user(self):
        """Тест создания перевала с существующим пользователем"""
        # Пользователь уже создан в setUp
        create_data = self.create_pereval_data.copy()
        create_data['user']['email'] = 'user1@example.com'  # Существующий email

        response = self.client.post(
            self.submit_data_url,
            data=json.dumps(create_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что не создан новый пользователь
        user_count = User.objects.filter(email='user1@example.com').count()
        self.assertEqual(user_count, 1)  # Остался один пользователь

    def test_update_pereval_images_replacement(self):
        """Тест замены изображений при обновлении"""
        # Создаем перевал с изображением
        pereval = Pereval.objects.create(
            beauty_title="Перевал с изображениями",
            title="Тест замены",
            user=self.user1,
            coords=self.coords1,
            level=self.level1,
            status='new'
        )

        # Добавляем начальное изображение
        image = Image.objects.create(
            pereval=pereval,
            title="Исходное изображение"
        )

        self.assertEqual(pereval.images.count(), 1)

        # Обновляем с новыми изображениями
        update_data = {
            "images": [
                {
                    "image": self.generate_test_image_base64(),
                    "title": "Новое изображение 1"
                },
                {
                    "image": self.generate_test_image_base64(),
                    "title": "Новое изображение 2"
                }
            ]
        }

        response = self.client.patch(
            self.submit_data_detail_url(pereval.id),
            data=json.dumps(update_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что старые изображения удалены, новые добавлены
        pereval.refresh_from_db()
        self.assertEqual(pereval.images.count(), 2)

        image_titles = list(pereval.images.values_list('title', flat=True))
        self.assertIn("Новое изображение 1", image_titles)
        self.assertIn("Новое изображение 2", image_titles)

    def test_pereval_serialization_format(self):
        """Тест формата сериализации перевала"""
        response = self.client.get(self.submit_data_detail_url(self.pereval1.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['data']

        # Проверяем структуру ответа
        required_fields = [
            'id', 'beauty_title', 'title', 'other_titles', 'connect',
            'add_time', 'status', 'user', 'coords', 'level', 'images'
        ]

        for field in required_fields:
            self.assertIn(field, data)

        # Проверяем структуру пользователя
        user_fields = ['email', 'fam', 'name', 'otc', 'phone']
        for field in user_fields:
            self.assertIn(field, data['user'])

        # Проверяем структуру координат
        coord_fields = ['latitude', 'longitude', 'height']
        for field in coord_fields:
            self.assertIn(field, data['coords'])

        # Проверяем структуру уровня
        level_fields = ['winter', 'summer', 'autumn', 'spring']
        for field in level_fields:
            self.assertIn(field, data['level'])


class ErrorHandlingTests(APITestCase):
    """Тесты обработки ошибок"""

    def setUp(self):
        self.client = APIClient()
        self.submit_data_url = reverse('submit-data-list')

    def test_malformed_json(self):
        """Тест обработки некорректного JSON"""
        response = self.client.post(
            self.submit_data_url,
            data="Это не JSON",
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_base64_image(self):
        """Тест обработки некорректного base64 изображения"""
        invalid_data = {
            "beauty_title": "Тест",
            "title": "Тест",
            "user": {
                "email": "test@example.com",
                "fam": "Тест",
                "name": "Тест",
                "phone": "+79991234567"
            },
            "coords": {
                "latitude": 55.755826,
                "longitude": 37.617300,
                "height": 150
            },
            "level": {
                "winter": "1A"
            },
            "images": [
                {
                    "image": "data:image/jpeg;base64,INVALID_BASE64_DATA",
                    "title": "Некорректное изображение"
                }
            ]
        }

        response = self.client.post(
            self.submit_data_url,
            data=json.dumps(invalid_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)


# Запуск тестов
if __name__ == '__main__':
    import django

    django.setup()
    from django.test.utils import get_runner
    from django.conf import settings

    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['pereval_app'])

    if failures:
        print(f"\n{failures} тестов не прошли")
    else:
        print("\nВсе тесты прошли успешно!")