# Django REST reCAPTCHA

**Django REST reCAPTCHA v2 and v3 field serializer**

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Requirements

Tested with:

* Python: 3.7, 3.8
* Django: 2.2
* Django REST framework: 3.10

# Installation

1. [Sign up for reCAPTCHA](https://www.google.com/recaptcha/)

2. Install with `pip install drf-recaptcha`

3. Add `"drf_recaptcha"` to your `INSTALLED_APPS` settings.

4. Set in settings `DRF_RECAPTCHA_SECRET_KEY`

```python
INSTALLED_APPS = [
   ...,
   "drf_recaptcha",
   ...,
]

...

DRF_RECAPTCHA_SECRET_KEY = "YOUR SECRET KEY"
```

# Usage

```python
from rest_framework.serializers import Serializer
from drf_recaptcha.fields import ReCaptchaV2Field, ReCaptchaV3Field

class V2Serializer(Serializer):
    recaptcha = ReCaptchaV2Field()
    ...

class V3Serializer(Serializer):
    recaptcha = ReCaptchaV3Field(action="example")
    ...

class V3WithScoreSerializer(Serializer):
    recaptcha = ReCaptchaV3Field(
        action="example",
        required_score=0.6,
    )
    ...
```

# Settings

`DRF_RECAPTCHA_SECRET_KEY` - must be set.

`DRF_RECAPTCHA_DEFAULT_V3_SCORE` - by default: `0.5`

`DRF_RECAPTCHA_ACTION_V3_SCORES` - by default: `{}`, you can define specific score for each action e.g. `{"login": 0.6, "feedback": 0.3"}`

`DRF_RECAPTCHA_DOMAIN` - by default: `www.google.com`

`DRF_RECAPTCHA_PROXY` - by default: `{}` e.g. `{'http': 'http://127.0.0.1:8000', 'https': 'https://127.0.0.1:8000'}`

`DRF_RECAPTCHA_VERIFY_REQUEST_TIMEOUT` - by default: `10`

# Priority of score value

1. Value in argument `required_score` of field, if not defined then
2. Value for action in settings `DRF_RECAPTCHA_ACTION_V3_SCORES`, if not defined then
3. Default value in settings `DRF_RECAPTCHA_DEFAULT_V3_SCORE`, if not defined then
4. Default value 0.5

# Testing

Set `DRF_RECAPTCHA_TESTING=True` in settings, no request to Google, no warnings, `DRF_RECAPTCHA_SECRET_KEY` is not required, set returning verification result in setting below.

`DRF_RECAPTCHA_TESTING_PASS=True|False` - all responses are pass, default `True`.

Use `from django.test import override_settings`

# Credits

[timeforimage.ru](https://timeforimage.ru) 

[django-recaptcha](https://github.com/praekelt/django-recaptcha)

reCAPTCHA copyright 2012 Google.
