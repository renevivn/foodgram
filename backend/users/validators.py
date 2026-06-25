from django.core.exceptions import ValidationError
from users.constants import RESERVED_USERNAME_ME


def validate_username_not_me(username):
    """Запрещает использовать конкретные username."""
    if username == RESERVED_USERNAME_ME:
        raise ValidationError(
            f'Использовать username "{RESERVED_USERNAME_ME}" запрещено.'
        )
