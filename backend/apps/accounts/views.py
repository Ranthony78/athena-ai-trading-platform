from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.text import slugify
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .registration import (
    CLOSED,
    CLOSED_MESSAGE,
    INACTIVE_MESSAGE,
    OPEN,
    PENDING_MESSAGE,
    notify_staff_of_pending_user,
    notify_user_of_activation,
    registration_mode,
)
from .serializers import (
    LoginSerializer,
    ManagedUserSerializer,
    PasswordResetConfirmSerializer,
    ProfileUpdateSerializer,
    RegistrationSerializer,
    UserSerializer,
)
from .token_utils import revoke_user_tokens

User = get_user_model()


def auth_response(user, message, response_status=status.HTTP_200_OK):
    refresh = RefreshToken.for_user(user)
    return Response(
        {
            "success": True,
            "message": message,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        },
        status=response_status,
    )


def closed_response():
    return Response(
        {"success": False, "message": CLOSED_MESSAGE, "code": "registration_closed"},
        status=status.HTTP_403_FORBIDDEN,
    )


def pending_response():
    # 202: the request was accepted, but nothing is usable until staff approve.
    return Response(
        {"success": True, "pending_approval": True, "message": PENDING_MESSAGE},
        status=status.HTTP_202_ACCEPTED,
    )


class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        return auth_response(user, "Login successful.")


class RegistrationAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def post(self, request):
        mode = registration_mode()
        if mode == CLOSED:
            # Refuse before validating so a closed door reveals nothing about
            # which usernames or emails already exist.
            return closed_response()

        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if mode == OPEN:
            user = serializer.save()
            return auth_response(
                user, "Account created successfully.", status.HTTP_201_CREATED
            )

        # "approval": save the account switched off and issue no tokens.
        user = serializer.save(is_active=False)
        notify_staff_of_pending_user(user)
        return pending_response()


class RegistrationModeAPIView(APIView):
    """GET /api/accounts/registration/ - lets the sign-in page adapt to the policy."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"success": True, "mode": registration_mode()})


class GoogleLoginAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        client_id = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "")
        credential = request.data.get("credential")
        if not client_id:
            return Response(
                {"success": False, "message": "Google sign-in is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if not credential:
            return Response(
                {"success": False, "message": "Google credential is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token
        except ImportError:
            return Response(
                {
                    "success": False,
                    "message": "Google sign-in dependencies are unavailable.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            identity = id_token.verify_oauth2_token(
                credential, google_requests.Request(), client_id
            )
        except Exception:
            return Response(
                {
                    "success": False,
                    "message": "Google credential is invalid or expired.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = (identity.get("email") or "").strip().lower()
        if not email or not identity.get("email_verified"):
            return Response(
                {"success": False, "message": "A verified Google email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            mode = registration_mode()
            if mode == CLOSED:
                return closed_response()
            base_username = slugify(
                identity.get("name") or email.split("@")[0]
            ).replace("-", "_")[:140]
            username_seed = base_username or "google_user"
            username = username_seed
            suffix = 1
            while User.objects.filter(username__iexact=username).exists():
                username = f"{username_seed[:130]}_{suffix}"
                suffix += 1
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=(identity.get("given_name") or "")[:150],
                last_name=(identity.get("family_name") or "")[:150],
                is_email_verified=True,
                is_active=(mode == OPEN),
            )
            if mode != OPEN:
                notify_staff_of_pending_user(user)
                return pending_response()
        else:
            if not user.is_active:
                return Response(
                    {"success": False, "message": INACTIVE_MESSAGE},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if not user.is_email_verified:
                # Registration does not verify email, so whoever created this
                # account may not own the address. Google has just proven the
                # real owner, so discard any password and sessions held by
                # the registrant before handing the account over; otherwise
                # they keep access to an account the owner now uses.
                user.set_unusable_password()
                user.is_email_verified = True
                user.save(update_fields=["password", "is_email_verified"])
                revoke_user_tokens(user)

        return auth_response(user, "Google sign-in successful.")


class ManagedUserListAPIView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ManagedUserSerializer
    filter_backends = [SearchFilter]
    search_fields = ["username", "email", "first_name", "last_name"]

    def get_queryset(self):
        """
        Optional ?status= filter:
          pending  - inactive and never signed in (waiting for approval)
          active   - can sign in
          inactive - switched off (includes pending)
        """
        users = User.objects.all().order_by("-date_joined", "id")
        wanted = self.request.query_params.get("status")
        if wanted == "pending":
            users = users.filter(is_active=False, last_login__isnull=True)
        elif wanted == "active":
            users = users.filter(is_active=True)
        elif wanted == "inactive":
            users = users.filter(is_active=False)
        return users


class ManagedUserStatusAPIView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, user_id):
        is_active = request.data.get("is_active")
        if not isinstance(is_active, bool):
            return Response(
                {"success": False, "message": "is_active must be true or false."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"success": False, "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.pk == request.user.pk and not is_active:
            return Response(
                {
                    "success": False,
                    "message": "You cannot deactivate your own account.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.is_superuser and not request.user.is_superuser and not is_active:
            return Response(
                {
                    "success": False,
                    "message": "Only a superuser can deactivate another superuser.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        was_active = user.is_active
        user.is_active = is_active
        user.save(update_fields=["is_active"])
        if is_active and not was_active:
            # Approval (or re-activation): tell the user they can sign in now.
            notify_user_of_activation(user)
        return Response(
            {"success": True, "user": ManagedUserSerializer(user).data},
            status=status.HTTP_200_OK,
        )


class ManagedUserPasswordResetAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"success": False, "message": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not user.email:
            return Response(
                {
                    "success": False,
                    "message": "This account does not have an email address.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user.is_active:
            return Response(
                {
                    "success": False,
                    "message": "Activate this account before sending a password reset link.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?uid={uid}&token={token}"
        display_name = user.first_name or user.username
        try:
            send_mail(
                subject="Reset your Athena account password",
                message=(
                    f"Hi {display_name},\n\n"
                    f"An administrator requested a password reset for your Athena account. "
                    f"Use this link to choose a new password. It expires and becomes invalid after the password is changed:\n\n{reset_url}\n\n"
                    "If you did not expect this email, contact your administrator."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception:
            return Response(
                {
                    "success": False,
                    "message": "The reset email could not be sent. Check the email server configuration.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "success": True,
                "message": "Password reset instructions were sent to the user's email.",
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user_id = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = User.objects.get(pk=user_id)
        except (
            TypeError,
            ValueError,
            OverflowError,
            UnicodeDecodeError,
            User.DoesNotExist,
        ):
            return Response(
                {
                    "success": False,
                    "message": "This password reset link is invalid or expired.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = serializer.validated_data["token"]
        if not user.is_active or not default_token_generator.check_token(user, token):
            return Response(
                {
                    "success": False,
                    "message": "This password reset link is invalid or expired.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(serializer.validated_data["new_password"], user=user)
        except ValidationError as error:
            return Response(
                {"success": False, "message": error.messages[0]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        # A reset is often a response to a compromised account: make sure any
        # existing session cannot be renewed with the old credentials.
        revoke_user_tokens(user)
        return Response(
            {"success": True, "message": "Password updated. You can now sign in."},
            status=status.HTTP_200_OK,
        )


class ThrottledTokenRefreshView(TokenRefreshView):
    """POST /api/accounts/token/refresh/ — rotates the refresh token."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "refresh"


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "success": True,
                "user": UserSerializer(request.user).data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        # Always the signed-in user; there is no way to name someone else.
        serializer = ProfileUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "success": True,
                "message": "Profile updated.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {
                    "success": False,
                    "message": "Refresh token is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {
                    "success": True,
                    "message": "Logout successful.",
                },
                status=status.HTTP_200_OK,
            )

        except Exception:
            return Response(
                {
                    "success": False,
                    "message": "Invalid refresh token.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
