# Django REST reCAPTCHA

**Django REST reCAPTCHA v2 and v3 field serializer**

[![CI](https://github.com/llybin/drf-recaptcha/workflows/tests/badge.svg)](https://github.com/llybin/drf-recaptcha/actions)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/a9b44d24cba74c75bca6472b2ee8da67)](https://www.codacy.com/app/llybin/drf-recaptcha?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=llybin/drf-recaptcha&amp;utm_campaign=Badge_Grade)
[![Codacy Badge](https://api.codacy.com/project/badge/Coverage/a9b44d24cba74c75bca6472b2ee8da67)](https://www.codacy.com/app/llybin/drf-recaptcha?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=llybin/drf-recaptcha&amp;utm_campaign=Badge_Coverage)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI](https://img.shields.io/pypi/v/drf-recaptcha)](https://pypi.org/project/drf-recaptcha/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/drf-recaptcha)](https://pypi.org/project/drf-recaptcha/)
[![PyPI - License](https://img.shields.io/pypi/l/drf-recaptcha)](https://pypi.org/project/drf-recaptcha/)

## Requirements

*   Python: 3.6, 3.7, 3.8, 3.9, 3.10
*   Django: 2.2, 3.1, 3.2, 4.0
*   DRF: 3.9, 3.10, 3.11, 3.12

## Installation

1.  [Sign up for reCAPTCHA](https://www.google.com/recaptcha/)
2.  Install with `pip install drf-recaptcha`
3.  Add `"drf_recaptcha"` to your `INSTALLED_APPS` settings.
4.  Set in settings `DRF_RECAPTCHA_SECRET_KEY`

```python
INSTALLED_APPS = [
   ...,
   "drf_recaptcha",
   ...,
]

...

DRF_RECAPTCHA_SECRET_KEY = "YOUR SECRET KEY"
```

## Usage

```python
from rest_framework.serializers import Serializer, ModelSerializer
from drf_recaptcha.fields import ReCaptchaV2Field, ReCaptchaV3Field
from feedback.models import Feedback


class V2Serializer(Serializer):
    recaptcha = ReCaptchaV2Field()
    ...

class GetOTPView(APIView):
    def post(self, request):
        serializer = V2Serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
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

class FeedbackSerializer(ModelSerializer):
    recaptcha = ReCaptchaV2Field()

    class Meta:
        model = Feedback
        fields = ("phone", "full_name", "email", "comment", "recaptcha")

    def validate(self, attrs):
        attrs.pop("recaptcha")
        ...
        return attrs
```

## Settings

`DRF_RECAPTCHA_SECRET_KEY` - set your Google reCAPTCHA secret key. Type: str.

`DRF_RECAPTCHA_DEFAULT_V3_SCORE` - by default: `0.5`. Type: float.

`DRF_RECAPTCHA_ACTION_V3_SCORES` - by default: `{}`. Type: dict. You can define specific score for each action e.g. `{"login": 0.6, "feedback": 0.3}`

`DRF_RECAPTCHA_DOMAIN` - by default: `www.google.com`. Type: str.

`DRF_RECAPTCHA_PROXY` - by default: `{}`. Type: dict. e.g. `{'http': 'http://127.0.0.1:8000', 'https': 'https://127.0.0.1:8000'}`

`DRF_RECAPTCHA_VERIFY_REQUEST_TIMEOUT` - by default: `10`. Type: int.

## reCAPTCHA v3

Validation is passed if the score value returned by Google is greater than or equal to required score.

Required score value: `0.0 - 1.0`

### Priority of score value

If not defined or zero in current item then value from next item.

1.  Value for action in settings `DRF_RECAPTCHA_ACTION_V3_SCORES`
2.  Value in argument `required_score` of field
3.  Default value in settings `DRF_RECAPTCHA_DEFAULT_V3_SCORE`
4.  Default value `0.5`

## Testing

Set `DRF_RECAPTCHA_TESTING=True` in settings, no request to Google, no warnings, `DRF_RECAPTCHA_SECRET_KEY` is not required, set returning verification result in setting below.

`DRF_RECAPTCHA_TESTING_PASS=True|False` - all responses are pass, default `True`.

Use `from django.test import override_settings`

## Credits

[django-recaptcha](https://github.com/praekelt/django-recaptcha)

reCAPTCHA copyright 2012 Google.
