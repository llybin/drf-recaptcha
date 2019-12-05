from django.conf import settings
from django.core.checks import Tags, Warning, register
from django.core.exceptions import ImproperlyConfigured

from drf_recaptcha.constants import TEST_V2_SECRET_KEY


@register(Tags.security)
def recaptcha_system_check(app_configs, **kwargs):
    errors = []

    is_testing = getattr(settings, "DRF_RECAPTCHA_TESTING", False)
    if is_testing:
        return errors

    secret_key = getattr(settings, "DRF_RECAPTCHA_SECRET_KEY", None)
    if not secret_key:
        raise ImproperlyConfigured("settings.DRF_RECAPTCHA_SECRET_KEY must be set.")

    if secret_key == TEST_V2_SECRET_KEY:
        errors.append(
            Warning(
                "Google test key for reCAPTCHA v2 is used now.\n"
                "If you use reCAPTCHA v2 - you will always get No CAPTCHA and all"
                " verification requests will pass.\n"
                "If you use reCAPTCHA v3 - all verification requests will fail.",
                hint="Update settings.DRF_RECAPTCHA_SECRET_KEY",
                id="drf_recaptcha.recaptcha_test_key_error",
            )
        )
    return errors
