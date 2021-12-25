"""
Django settings for iquise project.

Generated by 'django-admin startproject' using Django 1.11.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os, json, re, sys

DEBUG = False # Override in .env

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables directly to namespace
try:
    with open(os.path.join(BASE_DIR,'iquise','.env'),'r') as fid:
        # Replace any python escaped code in .env
        contents = fid.read()
        to_replace = [(m.groups()[0],m.start(),m.end()) for m in re.finditer(r'{{(.*?)}}',contents)]
        to_replace.reverse()
        for [val,start,end] in to_replace:
            evaled = eval(val)
            evaled = json.dumps(evaled)[1:-1] # Remove quotes
            contents = contents[0:start] + evaled + contents[end:]
        locals().update(json.loads(contents))
except:
    print("!!!!! Error loading your iquise/.env file. Easy to forget commas... !!!!!")
    raise

# SECURITY WARNING: keep the secret key used in production secret!
try:
    SECRET_KEY
except NameError:
    SECRET_FILE = os.path.join(BASE_DIR, 'iquise', 'secret.txt')
    try:
        SECRET_KEY = open(SECRET_FILE).read().strip()
    except IOError:
        try:
            import random
            SECRET_KEY = ''.join([random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
            secret = open(SECRET_FILE, 'w')
            secret.write(SECRET_KEY)
            secret.close()
        except IOError:
            Exception('Please create a %s file with random characters \
            to generate your secret key!' % SECRET_FILE)

# Application definition

INSTALLED_APPS = [
    'members',
    'website',
    'iquhack',
    'elections',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.forms',
    'easyaudit',
    'phonenumber_field',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middleware.iquise.LoginTokenMiddleware',
    'middleware.iquise.LoginRequiredMiddleware',
    'easyaudit.middleware.easyaudit.EasyAuditMiddleware',
]

ROOT_URLCONF = 'iquise.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'website.context_processors.basic_context',
            ],
        },
    },
]
FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'
WSGI_APPLICATION = 'iquise.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
# DATABASES comes from .env
if "test" in sys.argv:
    DATABASES = {"default": 
        {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "test_database.sqlite3",
        }
    }

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOG_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'INFO.log'),
            'maxBytes': 10*1024*1024,
            'backupCount': 5,
            'formatter': 'custom',
        },
    },
    'formatters':{
        'custom':{
            'format': '%(asctime)s %(levelname)-8s %(message)s',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# LoginRequiredMiddleware
REQUIRE_AUTH = False # only use on dev server
LOGIN_REDIRECT_URL = "members:profile"
LOGOUT_REDIRECT_URL = "website:index"
# LOGIN_EXEMPT_URLS = (r'^foo/',)

SERVER_EMAIL = "iquise-no-reply@rlehosting.mit.edu"
DEFAULT_FROM_EMAIL = SERVER_EMAIL
ADMINS = [("iQuISE Webmasters", "iquise-web@mit.edu")]
EMAIL_SUBJECT_PREFIX = "[iQuISE] "

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'EST'

USE_I18N = True

USE_L10N = True

USE_TZ = True

PHONENUMBER_DEFAULT_REGION = "US"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR,'iquise','static')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR,'iquise','media')

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

# Easyaudit
DJANGO_EASY_AUDIT_WATCH_REQUEST_EVENTS = False
DJANGO_EASY_AUDIT_ADMIN_SHOW_REQUEST_EVENTS = False
DJANGO_EASY_AUDIT_UNREGISTERED_CLASSES_EXTRA = ['auth.user', 'elections.vote']
