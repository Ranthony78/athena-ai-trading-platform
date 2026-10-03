from django.contrib.auth.backends import AllowAllUsersModelBackend
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User
from .registration import INACTIVE_MESSAGE


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        # The default backend returns None for inactive users, which would
        # make "wrong password" and "awaiting approval" look the same. This
        # one hashes the password once for every outcome (no timing
        # difference) and lets us say so only after the password is right.
        user = AllowAllUsersModelBackend().authenticate(
            request=None,
            username=attrs["username"],
            password=attrs["password"],
        )

        if user is None:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError(INACTIVE_MESSAGE)

        attrs["user"] = user
        return attrs


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
        ]

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return email

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone",
            "timezone",
            "is_staff",
        ]
        read_only_fields = fields


class ManagedUserSerializer(serializers.ModelSerializer):
    # Inactive and never signed in: a sign-up waiting for approval, as
    # opposed to an account that was switched off after being used.
    is_pending = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "is_pending",
            "is_staff",
            "date_joined",
            "last_login",
        ]
        read_only_fields = fields

    def get_is_pending(self, obj) -> bool:
        return not obj.is_active and obj.last_login is None


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True, validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        return attrs
