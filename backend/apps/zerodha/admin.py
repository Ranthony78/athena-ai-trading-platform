from django.contrib import admin

from .models import ZerodhaConfig, ZerodhaSession


@admin.register(ZerodhaConfig)
class ZerodhaConfigAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "is_connected",
        "connected_at",
        "token_expires_at",
        "mcp_url",
    )
    readonly_fields = (
        "access_token",
        "request_token",
        "is_connected",
        "connected_at",
        "token_expires_at",
    )
    search_fields = ("user__username",)


@admin.register(ZerodhaSession)
class ZerodhaSessionAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "zerodha_user_id",
        "zerodha_username",
        "status",
        "login_at",
        "expires_at",
    )
    list_filter = ("status",)
    readonly_fields = (
        "access_token",
        "login_at",
    )