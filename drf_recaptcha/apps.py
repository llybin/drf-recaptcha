from django.apps import AppConfig


class DRFreCaptchaConfig(AppConfig):
    name = "drf_recaptcha"
    verbose_name = "Django REST framework reCAPTCHA"

    def ready(self):  # noqa: PLR6301
        # Add System checks
        from .checks import recaptcha_system_check  # noqa: F401
