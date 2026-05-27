"""
Django settings for james_blog project.
UPDATED: Fixed image persistence by completely disabling HTML sanitization
"""
from decouple import config
import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", cast=bool, default=True)
ALLOWED_HOSTS = ['jameswoodhall.com', 'www.jameswoodhall.com', '*', '.vercel.app']

# Security settings - only in production
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'SAMEORIGIN'
SITE_ID = 1

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "blog.apps.BlogConfig",
    "taggit",
    'django_summernote',
    'django.contrib.sites',
    'django.contrib.sitemaps',
  
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'django.middleware.gzip.GZipMiddleware',
]

ROOT_URLCONF = "james_blog.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / 'blog' / 'templates',
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "blog.context_processors.author_profile",
            ],
        },
    },
]

WSGI_APPLICATION = "james_blog.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DATABASE_URL = config("DATABASE_URL", cast=str)

if DATABASE_URL is not None:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=300,
            conn_health_checks=True
        )
    }

CLOUDFLARE_R2_BUCKET = config("CLOUDFLARE_R2_BUCKET")
CLOUDFLARE_R2_ACCESS_KEY = config("CLOUDFLARE_R2_ACCESS_KEY")
CLOUDFLARE_R2_SECRET_KEY = config("CLOUDFLARE_R2_SECRET_KEY")
CLOUDFLARE_R2_BUCKET_ENDPOINT = config("CLOUDFLARE_R2_BUCKET_ENDPOINT")

R2_PUBLIC_CDN = "pub-9eb67c1c49104c9e8600d28556b91096.r2.dev"

CLOUDFLARE_R2_CONFIG_OPTIONS = {
    "bucket_name": CLOUDFLARE_R2_BUCKET,
    "access_key": CLOUDFLARE_R2_ACCESS_KEY,
    "secret_key": CLOUDFLARE_R2_SECRET_KEY,
    "endpoint_url": CLOUDFLARE_R2_BUCKET_ENDPOINT,
    "default_acl": "public-read",
    "signature_version": "s3v4",
    # Use public CDN URL for all file URLs (no expiring signed URLs)
    "custom_domain": R2_PUBLIC_CDN,
    "querystring_auth": False,
}

if DEBUG:
    # In development: serve static files from local filesystem so admin/summernote CSS loads
    STORAGES = {
        "default": {
            "BACKEND": "helpers.cloudflare.storages.MediaFileStorage",
            "OPTIONS": CLOUDFLARE_R2_CONFIG_OPTIONS
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        }
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "helpers.cloudflare.storages.MediaFileStorage",
            "OPTIONS": CLOUDFLARE_R2_CONFIG_OPTIONS
        },
        "staticfiles": {
            "BACKEND": "helpers.cloudflare.storages.StaticFileStorage",
            "OPTIONS": CLOUDFLARE_R2_CONFIG_OPTIONS
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_ROOT = os.path.join(BASE_DIR / 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static")
]
MEDIA_ROOT = BASE_DIR / 'media'

if DEBUG:
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'
else:
    STATIC_URL = 'https://pub-9eb67c1c49104c9e8600d28556b91096.r2.dev/static/'
    MEDIA_URL = 'https://pub-9eb67c1c49104c9e8600d28556b91096.r2.dev/media/'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email Configuration
SITE_NAME = 'James\' Blog'
SITE_URL = 'https://jameswoodhall.com'
SITE_LOGO = '/static/img/logo.png'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = "James <woodhalljames@gmail.com>"

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'blog': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# SUMMERNOTE CONFIGURATION
SUMMERNOTE_CONFIG = {
    # Use iframe mode (default for admin) - avoids jQuery conflicts with Django admin
    'iframe': True,

    # Storage configuration for image attachments inserted into content
    'attachment_storage_class': 'helpers.cloudflare.storages.MediaFileStorage',
    'attachment_filesize_limit': 10 * 1024 * 1024,  # 10MB
    'attachment_model': 'blog.SummernoteAttachment',
    'attachment_upload_to': 'summernote/%Y/%m/%d/',
    'attachment_require_authentication': True,
    'disable_attachment': False,

    # Disable server-side HTML sanitization so rich content is preserved
    'disable_server_side_validation': True,
    'sanitize': False,

    # Editor configuration
    'summernote': {
        'toolbar': [
            ['style', ['style']],
            ['font', ['bold', 'italic', 'underline', 'strikethrough', 'clear']],
            ['fontname', ['fontname']],
            ['fontsize', ['fontsize']],
            ['color', ['color']],
            ['para', ['ul', 'ol', 'paragraph']],
            ['height', ['height']],
            ['table', ['table']],
            ['insert', ['link', 'picture', 'video']],
            ['view', ['fullscreen', 'codeview', 'help']],
        ],
        'styleTags': ['p', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'pre'],
        'fontNames': ['Arial', 'Arial Black', 'Comic Sans MS', 'Courier New', 'Helvetica',
                      'Impact', 'Tahoma', 'Times New Roman', 'Verdana'],
        'fontSizes': ['8', '9', '10', '11', '12', '14', '16', '18', '20', '24', '28', '32', '36', '48'],
        'width': '100%',
        'height': '480',
        'codemirror': {
            'mode': 'htmlmixed',
            'lineNumbers': True,
            'theme': 'monokai',
        },
        'popover': {
            'image': [
                ['image', ['resizeFull', 'resizeHalf', 'resizeQuarter', 'resizeNone']],
                ['float', ['floatLeft', 'floatRight', 'floatNone']],
                ['remove', ['removeMedia']]
            ],
            'link': [
                ['link', ['linkDialogShow', 'unlink']]
            ],
            'table': [
                ['add', ['addRowDown', 'addRowUp', 'addColLeft', 'addColRight']],
                ['delete', ['deleteRow', 'deleteCol', 'deleteTable']],
            ],
        },
        'disableDragAndDrop': False,
        'shortcuts': True,
        'tabDisable': False,
    },

    'lazy': False,
    'airMode': False,
    'lang': 'en-US',
}

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'James_Cache',
    }
}