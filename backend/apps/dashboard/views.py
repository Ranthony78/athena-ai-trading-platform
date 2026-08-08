from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from shared.api_response import ApiResponse


class DashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        data = {
            "application": "Athena AI Trading Platform",
            "version": "1.0.0",
            "status": "Running",
            "user": {
                "username": request.user.username,
                "email": request.user.email,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
            },
            "modules": {
                "dashboard": True,
                "market_data": True,
                "paper_trading": True,
                "backtesting": True,
                "ai_engine": True,
                "strategies": True,
                "journal": True,
                "notifications": True,
                "knowledge": True,
            },
        }

        return ApiResponse.success(data=data)