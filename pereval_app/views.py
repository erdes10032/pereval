from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
import json
import logging
from .serializers import PerevalSerializer, PerevalUpdateSerializer
from .data_processor import PerevalDataProcessor
from .models import Pereval, User

logger = logging.getLogger(__name__)


class SubmitDataView(APIView):
    """
    API endpoint для добавления данных о перевале
    POST /submitData/
    """

    def post(self, request):
        try:
            # Логируем входящий запрос
            logger.info(f"Incoming request data: {request.data}")

            # Валидация данных
            serializer = PerevalSerializer(data=request.data)

            if not serializer.is_valid():
                logger.error(f"Validation errors: {serializer.errors}")
                return Response({
                    "status": 400,
                    "message": "Bad Request",
                    "id": None,
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data
            logger.info(f"Validated data: {validated_data}")

            # Проверяем данные пользователя
            if 'user' not in validated_data:
                logger.error("User data missing in validated_data")
                return Response({
                    "status": 400,
                    "message": "Данные пользователя обязательны",
                    "id": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # Обработка данных
            processor = PerevalDataProcessor()
            result = processor.submit_data(validated_data)  # Передаем validated_data

            # Формируем ответ
            if result["status"] == 200:
                return Response({
                    "status": 200,
                    "message": "Отправлено успешно",
                    "id": result["id"]
                }, status=status.HTTP_200_OK)
            elif result["status"] == 400:
                return Response({
                    "status": 400,
                    "message": result["message"],
                    "id": None
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "status": 500,
                    "message": result["message"] or "Internal server error",
                    "id": None
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except json.JSONDecodeError:
            logger.error("Invalid JSON in request")
            return Response({
                "status": 400,
                "message": "Invalid JSON format",
                "id": None
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response({
                "status": 500,
                "message": "Internal server error",
                "id": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetPerevalView(APIView):
    """
    API endpoint для получения данных о перевале по ID
    GET /submitData/<id>/
    """

    def get(self, request, pk):
        try:
            processor = PerevalDataProcessor()
            pereval_data = processor.get_pereval_by_id(pk)

            if not pereval_data:
                return Response({
                    "status": 404,
                    "message": f"Перевал с ID {pk} не найден",
                    "id": None
                }, status=status.HTTP_404_NOT_FOUND)

            return Response(pereval_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error getting pereval {pk}: {e}")
            return Response({
                "status": 500,
                "message": "Internal server error",
                "id": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdatePerevalView(APIView):
    """
    API endpoint для обновления данных о перевале
    PATCH /submitData/<id>/
    """

    def patch(self, request, pk):
        try:
            # Логируем входящий запрос
            logger.info(f"Update request for id {pk}: {request.data}")

            # Валидация данных
            serializer = PerevalUpdateSerializer(data=request.data, partial=True)

            if not serializer.is_valid():
                logger.error(f"Validation errors: {serializer.errors}")
                return Response({
                    "state": 0,
                    "message": f"Ошибка валидации: {serializer.errors}"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Проверяем, пытаются ли изменить данные пользователя
            if 'user' in request.data:
                return Response({
                    "state": 0,
                    "message": "Изменение данных пользователя запрещено"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Обработка данных
            processor = PerevalDataProcessor()
            result = processor.update_pereval(pk, serializer.validated_data)

            if result["state"] == 1:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except json.JSONDecodeError:
            logger.error("Invalid JSON in update request")
            return Response({
                "state": 0,
                "message": "Invalid JSON format"
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Unexpected error in update: {e}")
            return Response({
                "state": 0,
                "message": "Internal server error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetPerevalsByEmailView(APIView):
    """
    API endpoint для получения всех перевалов по email пользователя
    GET /submitData/?user__email=<email>
    """

    def get(self, request):
        try:
            email = request.query_params.get('user__email')

            if not email:
                return Response({
                    "status": 400,
                    "message": "Не указан email пользователя",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            processor = PerevalDataProcessor()
            perevals = processor.get_perevals_by_email(email)

            if not perevals:
                return Response({
                    "status": 404,
                    "message": f"Перевалы для пользователя с email {email} не найдены",
                    "data": []
                }, status=status.HTTP_404_NOT_FOUND)

            return Response({
                "status": 200,
                "message": f"Найдено {len(perevals)} перевалов",
                "data": perevals
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error getting perevals by email: {e}")
            return Response({
                "status": 500,
                "message": "Internal server error",
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)