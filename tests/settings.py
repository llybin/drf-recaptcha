SECRET_KEY = "TEST_SECRET_KEY"

INSTALLED_APPS = [
    "drf_recaptcha",
]

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "test.sqlite3"}
}

DRF_RECAPTCHA_SECRET_KEY = "TEST_DRF_RECAPTCHA_SECRET_KEY"
