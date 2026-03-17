import os
from pathlib import Path
from django.contrib.messages import constants as messages
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ======================
# SECURITY
# ======================
# Pulls from environment variable in production, falls back to this string locally
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-fallback-key-for-local-only')

# Safely converts the environment variable string 'True'/'False' into a Python boolean
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = [
    'ecochallengehub.online',
    'www.ecochallengehub.online',
    'gamified-education.onrender.com',
    'localhost',
    '127.0.0.1'
]

# Render automatically sets this environment variable. 
# Adding it ensures Render's internal routing works flawlessly.
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# ======================
# INSTALLED APPS
# ======================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',

    'whitenoise.runserver_nostatic',  # for static handling
    'django.contrib.staticfiles',

    # Custom apps
    'apps.accounts',
    'apps.quizzes',
    'apps.dashboard',
]

# ======================
# MIDDLEWARE
# ======================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # WhiteNoise MUST be exactly here (just below SecurityMiddleware)
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ecoquest.urls'

# ======================
# TEMPLATES
# ======================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ecoquest.wsgi.application'

# ======================
# DATABASE (UPDATED FOR RENDER)
# ======================
DATABASES = {
    # dj_database_url will automatically look for the 'DATABASE_URL' environment 
    # variable on Render. If it doesn't find it (like on your local PC), 
    # it uses the local SQLite file.
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
        conn_max_age=600
    )
}

# ======================
# PASSWORD VALIDATION
# ======================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ======================
# INTERNATIONALIZATION
# ======================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ======================
# STATIC FILES
# ======================
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise storage engine for compression and caching
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ======================
# MEDIA FILES
# ======================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ======================
# DEFAULTS
# ======================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ======================
# CUSTOM USER MODEL
# ======================
AUTH_USER_MODEL = 'accounts.User'

# ======================
# AUTH REDIRECTS
# ======================
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard:student_dashboard'
LOGOUT_REDIRECT_URL = 'index'

# ======================
# MESSAGES
# ======================
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}