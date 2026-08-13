from django.conf import settings
from django.core import checks

from drf_recaptcha.constants import TEST_V2_SECRET_KEY
from drf_recaptcha.validators import get_credential_from_settings

SECRET_KEY_SETTING = "DRF_RECAPTCHA_SECRET_KEY"  # noqa: S105
ENTERPRISE_SETTINGS = (
    "DRF_RECAPTCHA_ENTERPRISE_PROJECT_ID",
    "DRF_RECAPTCHA_ENTERPRISE_SITE_KEY",
)


def get_required_credential_settings() -> tuple[str, ...]:
    # Defining either Enterprise setting is what marks a project as using
    # Enterprise, even when it is defined empty — which is what a deployment
    # reading unset environment variables into settings ends up with, and the
    # case worth reporting.
    if any(hasattr(settings, setting) for setting in ENTERPRISE_SETTINGS):
        return (SECRET_KEY_SETTING, *ENTERPRISE_SETTINGS)

    return (SECRET_KEY_SETTING,)


def check_credentials_are_set() -> list[checks.CheckMessage]:
    # A warning rather than an error: the project runs without a credential, it
    # just refuses the submissions its captcha fields guard. An error would fail
    # every management command that runs checks, `migrate` included, and cost a
    # deployment its release as well.
    missing = [
        setting
        for setting in get_required_credential_settings()
        if not get_credential_from_settings(setting)
    ]
    if not missing:
        return []

    return [
        checks.Warning(
            "{} not set, so reCAPTCHA cannot verify a token and every field will"
            " reject its submission.".format(
                ", ".join(f"settings.{setting}" for setting in missing),
            ),
            hint=(
                "Configure the reCAPTCHA credentials, or set"
                " settings.DRF_RECAPTCHA_TESTING=True to accept every token"
                " without asking Google."
            ),
            id="drf_recaptcha.W001",
        ),
    ]


def check_test_key_is_not_used() -> list[checks.CheckMessage]:
    if get_credential_from_settings(SECRET_KEY_SETTING) != TEST_V2_SECRET_KEY:
        return []

    return [
        checks.Warning(
            "Google test key for reCAPTCHA v2 is used now.\n"
            "If you use reCAPTCHA v2 - you will always get No CAPTCHA and all"
            " verification requests will pass.\n"
            "If you use reCAPTCHA v3 - all verification requests will fail.",
            hint=f"Update settings.{SECRET_KEY_SETTING}",
            id="drf_recaptcha.recaptcha_test_key_error",
        ),
    ]


@checks.register(checks.Tags.security)
def recaptcha_system_check(app_configs, **kwargs):
    is_testing = getattr(settings, "DRF_RECAPTCHA_TESTING", False)
    if is_testing:
        return []

    return [*check_credentials_are_set(), *check_test_key_is_not_used()]
