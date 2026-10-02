from django.urls import path
from .views import GoogleLoginAPIView, LoginAPIView, LogoutAPIView, ManagedUserListAPIView, ManagedUserPasswordResetAPIView, ManagedUserStatusAPIView, PasswordResetConfirmAPIView, ProfileAPIView, RegistrationAPIView, ThrottledTokenRefreshView

urlpatterns = [
    path("login/", LoginAPIView.as_view(), name="login"),
    path("register/", RegistrationAPIView.as_view(), name="register"),
    path("google/", GoogleLoginAPIView.as_view(), name="google-login"),
    path("users/", ManagedUserListAPIView.as_view(), name="user-management-list"),
    path("users/<int:user_id>/status/", ManagedUserStatusAPIView.as_view(), name="user-management-status"),
    path("users/<int:user_id>/password-reset/", ManagedUserPasswordResetAPIView.as_view(), name="user-management-password-reset"),
    path("password-reset/confirm/", PasswordResetConfirmAPIView.as_view(), name="password-reset-confirm"),
    path("profile/", ProfileAPIView.as_view(), name="profile"),
    path("token/refresh/", ThrottledTokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
]
