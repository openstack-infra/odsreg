# Django settings for odsreg project.
#
# Copyright 2011 Thierry Carrez <thierry@openstack.org>
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os


PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SERVE_STATIC = True

SITE_ROOT = 'http://summit.openstack.org'

DATABASES = {
    'default': {
        'NAME': 'summit.db',
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

SITE_ID = 1

STATIC_URL = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'changemeInLocalSettings'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'odsreg.cfp.middleware.EventMiddleware',
)

ROOT_URLCONF = 'odsreg.urls'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_openid_auth',
    'django.contrib.admin',
    'odsreg.cfp',
    'odsreg.scheduling',
]

AUTHENTICATION_BACKENDS = (
    'django_openid_auth.auth.OpenIDBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# Should users be created when new OpenIDs are used to log in?
OPENID_CREATE_USERS = True
OPENID_STRICT_USERNAMES = True

# Can we reuse existing users?
OPENID_REUSE_USERS = True

# When logging in again, should we overwrite user details based on
# data received via Simple Registration?
OPENID_UPDATE_DETAILS_FROM_SREG = True

# If set, always use this as the identity URL rather than asking the
# user.  This only makes sense if it is a server URL.
OPENID_SSO_SERVER_URL = 'https://login.launchpad.net/'

# Tell django.contrib.auth to use the OpenID signin URLs.
LOGIN_URL = '/openid/login'
LOGIN_REDIRECT_URL = '/'

# Override settings with local ones.
try:
    from local_settings import *
except ImportError:
    pass
