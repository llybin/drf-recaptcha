from django.apps import AppConfig


class DRFreCaptchaConfig(AppConfig):
    name = "drf_recaptcha"
    verbose_name = "Django REST framework reCAPTCHA"

    def ready(self):
        # Add System checks
        from .checks import recaptcha_system_check  # NOQA
