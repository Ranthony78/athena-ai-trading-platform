from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger",),
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    path("api/market/", include("apps.market_data.api.urls"),),
    path("api/strategies/", include("apps.strategies.api.urls")),
    path("api/ai/", include("apps.ai_engine.api.urls")),
    path("api/paper/", include("apps.paper_trading.api.urls")),
    path("api/journal/", include("apps.journal.api.urls")),
    path("api/backtest/", include("apps.backtesting.api.urls")),
    path("api/knowledge/", include("apps.knowledge.api.urls")),
    path("api/notifications/", include("apps.notifications.api.urls")),
    path("api/zerodha/", include("apps.zerodha.api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)