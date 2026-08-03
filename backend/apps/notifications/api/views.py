import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse

from ..services.alert_service import AlertService
from ..services.notification_service import NotificationService
from .serializers import (
    AlertCreateSerializer,
    AlertSerializer,
    NotificationPreferenceSerializer,
    NotificationSerializer,
)

logger = logging.getLogger(__name__)


class NotificationListAPIView(APIView):
    """
    GET /api/notifications/
    Return notifications for the user.

    Query params:
        unread=1  — unread only
        limit=50  — max results
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            unread_only = request.query_params.get("unread") == "1"
            limit = int(request.query_params.get("limit", 50))

            notifications = NotificationService.get_notifications(
                user=request.user,
                unread_only=unread_only,
                limit=limit,
            )
            unread_count = NotificationService.get_unread_count(request.user)

            serializer = NotificationSerializer(notifications, many=True)
            return ApiResponse.success(
                data={
                    "notifications": serializer.data,
                    "unread_count": unread_count,
                }
            )
        except Exception as e:
            logger.error(f"NotificationListAPIView error: {e}")
            return ApiResponse.error(message="Failed to fetch notifications.")


class NotificationReadAPIView(APIView):
    """
    POST /api/notifications/<id>/read/
    Mark a notification as read.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        result = NotificationService.mark_read(pk, request.user)
        if result["success"]:
            return ApiResponse.success(message="Notification marked as read.")
        return ApiResponse.error(message=result["message"])


class NotificationReadAllAPIView(APIView):
    """
    POST /api/notifications/read-all/
    Mark all notifications as read.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = NotificationService.mark_all_read(request.user)
        return ApiResponse.success(
            data={"marked_read": count},
            message=f"{count} notifications marked as read.",
        )


class NotificationPreferenceAPIView(APIView):
    """
    GET /api/notifications/preferences/
    PUT /api/notifications/preferences/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        prefs = NotificationService.get_preferences(request.user)
        serializer = NotificationPreferenceSerializer(prefs)
        return ApiResponse.success(serializer.data)

    def put(self, request):
        serializer = NotificationPreferenceSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        try:
            prefs = NotificationService.update_preferences(
                user=request.user,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=NotificationPreferenceSerializer(prefs).data,
                message="Preferences updated.",
            )
        except Exception as e:
            logger.error(f"NotificationPreferenceAPIView PUT error: {e}")
            return ApiResponse.error(message="Failed to update preferences.")


class AlertListAPIView(APIView):
    """
    GET  /api/notifications/alerts/  — list active alerts
    POST /api/notifications/alerts/  — create alert
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            alerts = AlertService.get_alerts(request.user)
            serializer = AlertSerializer(alerts, many=True)
            return ApiResponse.success(serializer.data)
        except Exception as e:
            logger.error(f"AlertListAPIView GET error: {e}")
            return ApiResponse.error(message="Failed to fetch alerts.")

    def post(self, request):
        serializer = AlertCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.error(
                message="Invalid data.",
                errors=serializer.errors,
            )
        try:
            alert = AlertService.create_alert(
                user=request.user,
                data=serializer.validated_data,
            )
            return ApiResponse.success(
                data=AlertSerializer(alert).data,
                message="Alert created.",
            )
        except Exception as e:
            logger.error(f"AlertListAPIView POST error: {e}")
            return ApiResponse.error(message="Failed to create alert.")


class AlertCancelAPIView(APIView):
    """
    POST /api/notifications/alerts/<id>/cancel/
    Cancel an active alert.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        result = AlertService.cancel_alert(request.user, pk)
        if result["success"]:
            return ApiResponse.success(message=result["message"])
        return ApiResponse.error(message=result["message"])


class AlertCheckAPIView(APIView):
    """
    POST /api/notifications/alerts/check/
    Manually trigger alert checking against current prices.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            service = AlertService()
            triggered = service.check_all_alerts()
            return ApiResponse.success(
                data={"triggered": triggered},
                message=f"{triggered} alerts triggered.",
            )
        except Exception as e:
            logger.error(f"AlertCheckAPIView error: {e}")
            return ApiResponse.error(message="Failed to check alerts.")