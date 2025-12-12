from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json
import logging

from .serializers import PerevalSerializer
from .data_processor import PerevalDataProcessor

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

            # Обработка данных
            processor = PerevalDataProcessor()
            result = processor.submit_data(serializer.validated_data)

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