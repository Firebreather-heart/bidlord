from django.core.exceptions import ValidationError


class PasswordStrengthValidator:
    def __init__(self) -> None:
        self.min_length = 8 

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                f"Password must be at least {self.min_length} characters long."
            )
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password must contain at least one digit.")
        if not any(char.isalpha() for char in password):
            raise ValidationError("Password must contain at least one letter.")
        if not any(char in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for char in password):
            raise ValidationError("Password must contain at least one special character.")
        
    def get_help_text(self):
        return (
            f"Your password must be at least {self.min_length} characters long, "
            "contain at least one digit, one letter, and one special character."
        )