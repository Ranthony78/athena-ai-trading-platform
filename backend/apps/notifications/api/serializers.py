from rest_framework import serializers

from ..models import Alert, Notification, NotificationPreference


class NotificationPreferenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = NotificationPreference
        fields = [
            "id",
            "email_enabled",
            "telegram_enabled",
            "push_enabled",
            "telegram_chat_id",
            "telegram_username",
            "email_address",
            "notify_ai_signals",
            "notify_strategy_signals",
            "notify_price_alerts",
            "notify_trade_execution",
            "notify_market_open",
            "notify_market_close",
            "notify_daily_summary",
            "quiet_hours_enabled",
            "quiet_from",
            "quiet_until",
        ]


class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "channel",
            "status",
            "title",
            "message",
            "data",
            "is_read",
            "read_at",
            "sent_at",
            "created_at",
        ]


class AlertSerializer(serializers.ModelSerializer):

    class Meta:
        model = Alert
        fields = [
            "id",
            "symbol",
            "alert_type",
            "status",
            "target_value",
            "current_value",
            "message",
            "notify_email",
            "notify_telegram",
            "triggered_at",
            "triggered_value",
            "repeat",
            "expires_at",
            "created_at",
        ]


class AlertCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Alert
        fields = [
            "symbol",
            "alert_type",
            "target_value",
            "message",
            "notify_email",
            "notify_telegram",
            "repeat",
            "expires_at",
        ]