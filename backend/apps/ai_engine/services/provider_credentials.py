"""Resolve and securely store personal AI provider credentials."""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

from ..models import AIProviderCredential


PROVIDER_SETTINGS = {
    "gemini": ("Gemini", "GEMINI_API_KEY", "GEMINI_MODEL", "gemini-3.5-flash"),
    "kimi": ("Kimi", "KIMI_API_KEY", "KIMI_MODEL", "kimi-k3"),
    "claude": ("Claude", "ANTHROPIC_API_KEY", None, "claude-sonnet-4-6"),
    "groq": ("Groq", "GROQ_API_KEY", None, "llama-3.3-70b-versatile"),
    "mock": ("Development mock", None, None, "mock"),
}


class ProviderCredentialError(Exception):
    """A stored provider credential cannot be decrypted or used."""


class ProviderEncryptionUnavailable(Exception):
    """The server does not have a safe Django secret for credential encryption."""


class ProviderCredentialService:
    @staticmethod
    def _fernet():
        # Derive a dedicated encryption key from Django's secret without
        # introducing another secret that users must copy into .env.
        secret = str(settings.SECRET_KEY or "")
        if secret == "change-me" or len(secret) < 32:
            raise ProviderEncryptionUnavailable(
                "Set a unique DJANGO_SECRET_KEY of at least 32 characters before saving provider credentials."
            )
        material = (secret + ":athena-ai-provider-credentials:v1").encode()
        key = base64.urlsafe_b64encode(hashlib.sha256(material).digest())
        return Fernet(key)

    @classmethod
    def encrypt(cls, api_key):
        return cls._fernet().encrypt(api_key.encode("utf-8")).decode("ascii")

    @classmethod
    def decrypt(cls, encrypted_api_key):
        try:
            return cls._fernet().decrypt(encrypted_api_key.encode("ascii")).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError, ValueError) as exc:
            raise ProviderCredentialError(
                "Saved AI credentials cannot be decrypted. Re-enter the provider key."
            ) from exc

    @classmethod
    def save(cls, user, provider, api_key):
        credential, _ = AIProviderCredential.objects.update_or_create(
            user=user,
            defaults={
                "provider": provider,
                "encrypted_api_key": cls.encrypt(api_key),
            },
        )
        return credential

    @staticmethod
    def delete(user):
        AIProviderCredential.objects.filter(user=user).delete()

    @classmethod
    def describe(cls, user):
        personal = AIProviderCredential.objects.filter(user=user).first()
        if personal:
            name, _, model_setting, default_model = PROVIDER_SETTINGS[personal.provider]
            model = getattr(settings, model_setting, default_model) if model_setting else default_model
            return {
                "provider": personal.provider,
                "provider_name": name,
                "model": model,
                "configured": True,
                "credential_source": "personal",
                "personal_credential_saved": True,
                "is_mock": False,
            }
        config = cls.resolve()
        config.pop("api_key", None)
        config["credential_source"] = config.pop("source")
        config["personal_credential_saved"] = False
        return config

    @classmethod
    def resolve(cls, user=None):
        credential = None
        if user is not None and getattr(user, "is_authenticated", False):
            credential = AIProviderCredential.objects.filter(user=user).first()

        if credential:
            provider = credential.provider
            name, _, model_setting, default_model = PROVIDER_SETTINGS[provider]
            model = getattr(settings, model_setting, default_model) if model_setting else default_model
            return {
                "provider": provider,
                "provider_name": name,
                "model": model,
                "api_key": cls.decrypt(credential.encrypted_api_key),
                "source": "personal",
                "configured": True,
            }

        provider = str(getattr(settings, "AI_PROVIDER", "mock") or "mock").strip().lower()
        name, key_setting, model_setting, default_model = PROVIDER_SETTINGS.get(
            provider, (provider.title(), None, None, "unknown")
        )
        model = getattr(settings, model_setting, default_model) if model_setting else default_model
        api_key = getattr(settings, key_setting, "") if key_setting else ""
        return {
            "provider": provider,
            "provider_name": name,
            "model": model,
            "api_key": api_key,
            "source": "server" if api_key else "none",
            "configured": provider == "mock" or bool(api_key),
        }
