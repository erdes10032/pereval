from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
import logging
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import PerevalSerializer, PerevalUpdateSerializer
from .models import Pereval, User, Coords, Level, Image

logger = logging.getLogger(__name__)


class SubmitDataView(APIView):
    """
    API endpoint для:
    POST /submitData/ - создание записи
    GET /submitData/?user__email=<email> - получение записей по email
    """

    @swagger_auto_schema(
        operation_description="Получение списка перевалов по email пользователя",
        manual_parameters=[
            openapi.Parameter(
                'user__email',
                openapi.IN_QUERY,
                description="Email пользователя для фильтрации",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Успешный запрос",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'beauty_title': openapi.Schema(type=openapi.TYPE_STRING),
                                    'title': openapi.Schema(type=openapi.TYPE_STRING),
                                    'other_titles': openapi.Schema(type=openapi.TYPE_STRING),
                                    'connect': openapi.Schema(type=openapi.TYPE_STRING),
                                    'add_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                                    'user': openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'email': openapi.Schema(type=openapi.TYPE_STRING),
                                            'fam': openapi.Schema(type=openapi.TYPE_STRING),
                                            'name': openapi.Schema(type=openapi.TYPE_STRING),
                                            'otc': openapi.Schema(type=openapi.TYPE_STRING),
                                            'phone': openapi.Schema(type=openapi.TYPE_STRING),
                                        }
                                    ),
                                    'coords': openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'latitude': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                                            'longitude': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                                            'height': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        }
                                    ),
                                    'level': openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'winter': openapi.Schema(type=openapi.TYPE_STRING),
                                            'summer': openapi.Schema(type=openapi.TYPE_STRING),
                                            'autumn': openapi.Schema(type=openapi.TYPE_STRING),
                                            'spring': openapi.Schema(type=openapi.TYPE_STRING),
                                        }
                                    ),
                                    'images': openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                'image_url': openapi.Schema(type=openapi.TYPE_STRING),
                                                'title': openapi.Schema(type=openapi.TYPE_STRING),
                                            }
                                        )
                                    )
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Не указан email",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT)
                        )
                    }
                )
            ),
            500: openapi.Response(
                description="Внутренняя ошибка сервера",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT)
                        )
                    }
                )
            )
        }
    )
    def get(self, request):
        """GET метод - получение перевалов по email"""
        try:
            email = request.query_params.get('user__email')

            if not email:
                return Response({
                    "status": 400,
                    "message": "Не указан email пользователя",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            # Ищем все перевалы с таким email пользователя
            perevals = Pereval.objects.filter(
                user__email=email
            ).select_related(
                'user', 'coords', 'level'
            ).prefetch_related('images')

            if not perevals.exists():
                return Response({
                    "status": 200,
                    "message": f"Для пользователя с email {email} перевалы не найдены",
                    "data": []
                }, status=status.HTTP_200_OK)

            result = []
            for pereval in perevals:
                pereval_data = self._serialize_pereval(pereval, request)
                result.append(pereval_data)

            return Response({
                "status": 200,
                "message": f"Найдено {len(result)} перевалов",
                "data": result
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error getting perevals by email: {e}")
            return Response({
                "status": 500,
                "message": "Internal server error",
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="Создание новой записи о перевале",
        request_body=PerevalSerializer,
        responses={
            200: openapi.Response(
                description="Запись успешно создана",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            400: openapi.Response(
                description="Ошибка валидации",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'id': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'errors': openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            ),
            500: openapi.Response(
                description="Внутренняя ошибка сервера",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'id': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                    }
                )
            )
        }
    )
    def post(self, request):
        try:
            serializer = PerevalSerializer(data=request.data)

            if not serializer.is_valid():
                logger.error(f"Validation errors: {serializer.errors}")
                return Response({
                    "status": 400,
                    "message": "Bad Request",
                    "id": None,
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                # Обрабатываем пользователя
                user_data = serializer.validated_data.pop('user')
                user, created = User.objects.get_or_create(
                    email=user_data['email'],
                    defaults={
                        'fam': user_data['fam'],
                        'name': user_data['name'],
                        'otc': user_data.get('otc', ''),
                        'phone': user_data['phone']
                    }
                )

                # Обрабатываем координаты
                coords_data = serializer.validated_data.pop('coords')
                coords = Coords.objects.create(**coords_data)

                # Обрабатываем уровень сложности
                level_data = serializer.validated_data.pop('level')
                level = Level.objects.create(**level_data)

                # Обрабатываем изображения
                images_data = serializer.validated_data.pop('images')

                # Создаем перевал
                pereval = Pereval.objects.create(
                    user=user,
                    coords=coords,
                    level=level,
                    **serializer.validated_data,
                    status='new'
                )

                # Создаем изображения
                for img_data in images_data:
                    Image.objects.create(pereval=pereval, **img_data)

            return Response({
                "status": 200,
                "message": "Отправлено успешно",
                "id": pereval.id
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response({
                "status": 500,
                "message": "Internal server error",
                "id": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _serialize_pereval(self, pereval, request):
        """Сериализация объекта перевала"""
        # Получаем полный URL для изображений
        images_data = []
        for img in pereval.images.all():
            if img.image:
                # Формируем полный URL до изображения
                image_url = request.build_absolute_uri(img.image.url) if img.image else None
                images_data.append({
                    "image_url": image_url,
                    "title": img.title
                })

        return {
            "id": pereval.id,
            "beauty_title": pereval.beauty_title,
            "title": pereval.title,
            "other_titles": pereval.other_titles,
            "connect": pereval.connect,
            "add_time": pereval.add_time,
            "status": pereval.status,
            "user": {
                "email": pereval.user.email,
                "fam": pereval.user.fam,
                "name": pereval.user.name,
                "otc": pereval.user.otc,
                "phone": pereval.user.phone
            },
            "coords": {
                "latitude": float(pereval.coords.latitude),
                "longitude": float(pereval.coords.longitude),
                "height": pereval.coords.height
            },
            "level": {
                "winter": pereval.level.winter,
                "summer": pereval.level.summer,
                "autumn": pereval.level.autumn,
                "spring": pereval.level.spring
            },
            "images": images_data
        }


class PerevalDetailView(APIView):
    """
    API endpoint для:
    GET /submitData/<id>/ - получение перевала по ID
    PATCH /submitData/<id>/ - обновление перевала по ID
    """

    @swagger_auto_schema(
        operation_description="Получение информации о перевале по ID",
        responses={
            200: openapi.Response(
                description="Перевал найден",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'beauty_title': openapi.Schema(type=openapi.TYPE_STRING),
                                'title': openapi.Schema(type=openapi.TYPE_STRING),
                                'other_titles': openapi.Schema(type=openapi.TYPE_STRING),
                                'connect': openapi.Schema(type=openapi.TYPE_STRING),
                                'add_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                'status': openapi.Schema(type=openapi.TYPE_STRING),
                                'user': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                                        'fam': openapi.Schema(type=openapi.TYPE_STRING),
                                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                                        'otc': openapi.Schema(type=openapi.TYPE_STRING),
                                        'phone': openapi.Schema(type=openapi.TYPE_STRING),
                                    }
                                ),
                                'coords': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'latitude': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                                        'longitude': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                                        'height': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    }
                                ),
                                'level': openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'winter': openapi.Schema(type=openapi.TYPE_STRING),
                                        'summer': openapi.Schema(type=openapi.TYPE_STRING),
                                        'autumn': openapi.Schema(type=openapi.TYPE_STRING),
                                        'spring': openapi.Schema(type=openapi.TYPE_STRING),
                                    }
                                ),
                                'images': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'image_url': openapi.Schema(type=openapi.TYPE_STRING),
                                            'title': openapi.Schema(type=openapi.TYPE_STRING),
                                        }
                                    )
                                )
                            }
                        )
                    }
                )
            ),
            404: openapi.Response(
                description="Перевал не найден",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'id': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                    }
                )
            ),
            500: openapi.Response(
                description="Внутренняя ошибка сервера",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'id': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                    }
                )
            )
        }
    )
    def get(self, request, id):
        """GET метод - получение перевала по ID"""
        try:
            try:
                pereval = Pereval.objects.select_related(
                    'user', 'coords', 'level'
                ).prefetch_related('images').get(id=id)
            except Pereval.DoesNotExist:
                return Response({
                    "status": 404,
                    "message": f"Перевал с ID {id} не найден",
                    "id": None
                }, status=status.HTTP_404_NOT_FOUND)

            # Сериализуем данные
            images_data = []
            for img in pereval.images.all():
                if img.image:
                    # Формируем полный URL до изображения
                    image_url = request.build_absolute_uri(img.image.url) if img.image else None
                    images_data.append({
                        "image_url": image_url,
                        "title": img.title
                    })

            pereval_data = {
                "id": pereval.id,
                "beauty_title": pereval.beauty_title,
                "title": pereval.title,
                "other_titles": pereval.other_titles,
                "connect": pereval.connect,
                "add_time": pereval.add_time,
                "status": pereval.status,
                "user": {
                    "email": pereval.user.email,
                    "fam": pereval.user.fam,
                    "name": pereval.user.name,
                    "otc": pereval.user.otc,
                    "phone": pereval.user.phone
                },
                "coords": {
                    "latitude": float(pereval.coords.latitude),
                    "longitude": float(pereval.coords.longitude),
                    "height": pereval.coords.height
                },
                "level": {
                    "winter": pereval.level.winter,
                    "summer": pereval.level.summer,
                    "autumn": pereval.level.autumn,
                    "spring": pereval.level.spring
                },
                "images": images_data
            }

            return Response({
                "status": 200,
                "message": "Найдено",
                "data": pereval_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error getting pereval {id}: {e}")
            return Response({
                "status": 500,
                "message": "Internal server error",
                "id": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="Обновление данных о перевале",
        request_body=PerevalUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Запись успешно обновлена",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'state': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: openapi.Response(
                description="Ошибка валидации или редактирование запрещено",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'state': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            404: openapi.Response(
                description="Перевал не найден",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'state': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            500: openapi.Response(
                description="Внутренняя ошибка сервера",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'state': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            )
        }
    )
    def patch(self, request, id):
        """PATCH метод - обновление перевала"""
        try:
            # Проверяем существование перевала
            try:
                pereval = Pereval.objects.get(id=id)
            except Pereval.DoesNotExist:
                return Response({
                    "state": 0,
                    "message": f"Перевал с ID {id} не найден"
                }, status=status.HTTP_404_NOT_FOUND)

            # Проверяем статус - только 'new' можно редактировать
            if pereval.status != 'new':
                return Response({
                    "state": 0,
                    "message": f"Редактирование запрещено. Текущий статус: {pereval.get_status_display()}"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Валидация данных
            serializer = PerevalUpdateSerializer(data=request.data, partial=True)

            if not serializer.is_valid():
                logger.error(f"Validation errors: {serializer.errors}")
                return Response({
                    "state": 0,
                    "message": f"Ошибка валидации"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Проверяем, чтобы не было полей пользователя
            user_fields = ['email', 'fam', 'name', 'otc', 'phone', 'user']
            for field in user_fields:
                if field in request.data:
                    return Response({
                        "state": 0,
                        "message": f"Изменение данных пользователя запрещено"
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Проверяем вложенные данные пользователя в словаре
            if isinstance(request.data, dict):
                for key in request.data.keys():
                    if 'email' in str(key).lower() or 'phone' in str(key).lower():
                        return Response({
                            "state": 0,
                            "message": "Изменение данных пользователя запрещено"
                        }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                # Обновляем координаты
                if 'coords' in serializer.validated_data:
                    coords_data = serializer.validated_data.pop('coords')
                    for key, value in coords_data.items():
                        setattr(pereval.coords, key, value)
                    pereval.coords.save()

                # Обновляем уровень сложности
                if 'level' in serializer.validated_data:
                    level_data = serializer.validated_data.pop('level')
                    for key, value in level_data.items():
                        setattr(pereval.level, key, value)
                    pereval.level.save()

                # Обновляем изображения
                if 'images' in serializer.validated_data:
                    # Удаляем старые изображения (и их файлы)
                    for img in pereval.images.all():
                        img.delete()

                    # Создаем новые изображения
                    images_data = serializer.validated_data.pop('images')
                    for img_data in images_data:
                        Image.objects.create(pereval=pereval, **img_data)

                # Обновляем основные поля перевала
                for field, value in serializer.validated_data.items():
                    setattr(pereval, field, value)
                pereval.save()

            return Response({
                "state": 1,
                "message": "Запись успешно обновлена"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error in update: {e}")
            return Response({
                "state": 0,
                "message": f"Internal server error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)