from setuptools import find_packages, setup


def read(f):
    return open(f, encoding="utf-8").read()


setup(
    name="drf-recaptcha",
    version="2.2.2",
    description="Django rest framework recaptcha field serializer.",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Lev Lybin",
    author_email="lev.lybin@gmail.com",
    license="MIT",
    url="https://github.com/llybin/drf-recaptcha",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "django>=3.2,<4.2",
        "djangorestframework>=3.11,<4.0",
        "django-ipware>=2.1,<4.1",
    ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest", "pytest-django", "pytest-cov"],
    python_requires=">=3.7",
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "django",
        "drf",
        "rest",
        "django-rest-framework",
        "reCAPTCHA",
        "reCAPTCHA v2",
        "reCAPTCHA v3",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Environment :: Plugins",
        "Intended Audience :: Developers",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
