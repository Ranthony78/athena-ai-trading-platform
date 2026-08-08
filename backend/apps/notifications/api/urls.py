from django.urls import path

from .views import (
    AlertCancelAPIView,
    AlertCheckAPIView,
    AlertListAPIView,
    NotificationListAPIView,
    NotificationPreferenceAPIView,
    NotificationReadAllAPIView,
    NotificationReadAPIView,
)

urlpatterns = [

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------
    path(
        "",
        NotificationListAPIView.as_view(),
        name="notification-list",
    ),
    path(
        "<int:pk>/read/",
        NotificationReadAPIView.as_view(),
        name="notification-read",
    ),
    path(
        "read-all/",
        NotificationReadAllAPIView.as_view(),
        name="notification-read-all",
    ),
    path(
        "preferences/",
        NotificationPreferenceAPIView.as_view(),
        name="notification-preferences",
    ),

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------
    path(
        "alerts/",
        AlertListAPIView.as_view(),
        name="alert-list",
    ),
    path(
        "alerts/check/",
        AlertCheckAPIView.as_view(),
        name="alert-check",
    ),
    path(
        "alerts/<int:pk>/cancel/",
        AlertCancelAPIView.as_view(),
        name="alert-cancel",
    ),
]