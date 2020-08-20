import pytest
from django.core.exceptions import ImproperlyConfigured

from drf_recaptcha.checks import recaptcha_system_check
from drf_recaptcha.constants import TEST_V2_SECRET_KEY


def test_warning_no_secret_key(settings):
    settings.DRF_RECAPTCHA_SECRET_KEY = None

    with pytest.raises(ImproperlyConfigured) as exc_info:
        recaptcha_system_check(None)

    assert str(exc_info.value) == "settings.DRF_RECAPTCHA_SECRET_KEY must be set."


def test_silent_testing(settings):
    settings.DRF_RECAPTCHA_TESTING = True
    settings.DRF_RECAPTCHA_SECRET_KEY = None

    assert recaptcha_system_check(None) == []


def test_warning_test_secret_key(settings):
    settings.DRF_RECAPTCHA_SECRET_KEY = TEST_V2_SECRET_KEY

    errors = recaptcha_system_check(None)
    assert len(errors) == 1
    assert errors[0].hint == "Update settings.DRF_RECAPTCHA_SECRET_KEY"
