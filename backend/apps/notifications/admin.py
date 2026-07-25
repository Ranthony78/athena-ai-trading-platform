from django.contrib import admin

from .models import Alert, Notification, NotificationPreference


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "email_enabled",
        "telegram_enabled",
        "notify_ai_signals",
        "notify_strategy_signals",
        "notify_price_alerts",
    )
    search_fields = ("user__username",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "notification_type",
        "channel",
        "status",
        "title",
        "created_at",
    )
    list_filter = ("notification_type", "channel", "status")
    search_fields = ("user__username", "title")
    readonly_fields = ("sent_at", "read_at", "failed_reason")


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "symbol",
        "alert_type",
        "target_value",
        "current_value",
        "status",
        "triggered_at",
    )
    list_filter = ("alert_type", "status")
    search_fields = ("user__username", "symbol")