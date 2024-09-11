# Django REST reCAPTCHA

**Django REST reCAPTCHA v2 and v3 field serializer**

[![Donate](https://img.shields.io/github/sponsors/llybin?style=flat-square)](https://github.com/sponsors/llybin)
[![CI](https://github.com/llybin/drf-recaptcha/workflows/tests/badge.svg)](https://github.com/llybin/drf-recaptcha/actions)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/a9b44d24cba74c75bca6472b2ee8da67)](https://www.codacy.com/app/llybin/drf-recaptcha?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=llybin/drf-recaptcha&amp;utm_campaign=Badge_Grade)
[![Codacy Badge](https://api.codacy.com/project/badge/Coverage/a9b44d24cba74c75bca6472b2ee8da67)](https://www.codacy.com/app/llybin/drf-recaptcha?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=llybin/drf-recaptcha&amp;utm_campaign=Badge_Coverage)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI](https://img.shields.io/pypi/v/drf-recaptcha)](https://pypi.org/project/drf-recaptcha/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/drf-recaptcha)](https://pypi.org/project/drf-recaptcha/)
[![PyPI - License](https://img.shields.io/pypi/l/drf-recaptcha)](https://pypi.org/project/drf-recaptcha/)


## Requirements

* Python: 3.10, 3.11, 3.12
* Django: 4.2, 5.0, 5.1
* DRF: 3.14, 3.15

## Installation

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


class GetReCaptchaScore(APIView):
    def post(self, request):
        serializer = V3WithScoreSerializer(data=request.data, context={"request": request})
        serializer.is_valid()
        score = serializer.fields['recaptcha'].score
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


class DynamicContextSecretKey(APIView):
    def post(self, request):
        if request.platform == "android":
            recaptcha_secret_key = "SPECIAL_FOR_ANDROID"
        else:
            recaptcha_secret_key = "SPECIAL_FOR_IOS"
        serializer = WithReCaptchaSerializer(
            data=request.data,
            context={
                "request": request,
                "recaptcha_secret_key": recaptcha_secret_key,
            },
        )
        serializer.is_valid(raise_exception=True)
        ...


class DynamicContextSecretKey(GenericAPIView):
    serializer_class = WithReCaptchaSerializer

    def get_serializer_context(self):
        if self.request.platform == "android":
            recaptcha_secret_key = "SPECIAL_FOR_ANDROID"
        else:
            recaptcha_secret_key = "SPECIAL_FOR_IOS"
        context = super().get_serializer_context()
        context.update({"recaptcha_secret_key": recaptcha_secret_key})
        return context


class MobileSerializer(Serializer):
    recaptcha = ReCaptchaV3Field(secret_key="SPECIAL_MOBILE_KEY", action="feedback")
    ...
```

## Settings

`DRF_RECAPTCHA_SECRET_KEY` - set your Google reCAPTCHA secret key. Type: str.

`DRF_RECAPTCHA_DEFAULT_V3_SCORE` - by default: `0.5`. Type: float.

`DRF_RECAPTCHA_ACTION_V3_SCORES` - by default: `{}`. Type: dict. You can define specific score for each action e.g.
`{"login": 0.6, "feedback": 0.3}`

`DRF_RECAPTCHA_DOMAIN` - by default: `www.google.com`. Type: str.

`DRF_RECAPTCHA_PROXY` - by default: `{}`. Type: dict. e.g.
`{'http': 'http://127.0.0.1:8000', 'https': 'https://127.0.0.1:8000'}`

`DRF_RECAPTCHA_VERIFY_REQUEST_TIMEOUT` - by default: `10`. Type: int.

### Priority of secret_key value

1. settings `DRF_RECAPTCHA_SECRET_KEY`
2. the argument `secret_key` of field
3. request.context["recaptcha_secret_key"]

### Silence the check error

If you need to disable the error, you can do so using the django settings.

```python
SILENCED_SYSTEM_CHECKS = ['drf_recaptcha.checks.recaptcha_system_check']
```

## reCAPTCHA v3

Validation is passed if the score value returned by Google is greater than or equal to required score.

Required score value: `0.0 - 1.0`

### Priority of score value

If not defined or zero in current item then value from next item.

1. Value for action in settings `DRF_RECAPTCHA_ACTION_V3_SCORES`
2. Value in argument `required_score` of field
3. Default value in settings `DRF_RECAPTCHA_DEFAULT_V3_SCORE`
4. Default value `0.5`

## Testing

Set `DRF_RECAPTCHA_TESTING=True` in settings, no request to Google, no warnings, `DRF_RECAPTCHA_SECRET_KEY` is not
required, set returning verification result in setting below.

`DRF_RECAPTCHA_TESTING_PASS=True|False` - all responses are pass, default `True`.

Use `from django.test import override_settings`

## Credits

[django-recaptcha](https://github.com/praekelt/django-recaptcha)

reCAPTCHA copyright 2012 Google.
