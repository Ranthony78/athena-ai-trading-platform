from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)


def revoke_user_tokens(user) -> int:
    """
    Blacklist every refresh token issued to `user` so no existing session
    can be renewed. Access tokens already issued stay valid until they
    expire (SIMPLE_JWT ACCESS_TOKEN_LIFETIME).

    Returns how many tokens were newly revoked.
    """
    revoked = 0
    for token in OutstandingToken.objects.filter(user=user):
        _, created = BlacklistedToken.objects.get_or_create(token=token)
        revoked += int(created)
    return revoked
