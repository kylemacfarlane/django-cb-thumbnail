import os
import sys


DEBUG = True
DATABASE_ENGINE = 'sqlite3'
if sys.platform[0:3] == 'win':
    TEMP = os.environ.get('TEMP', '')
else:
    TEMP = '/tmp'
DATABASE_NAME = os.path.join(TEMP, 'thumbnail.db')
INSTALLED_APPS = [
    'cuddlybuddly.thumbnail',
    'cuddlybuddly.storage.s3',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites'
]
SITE_ID = 1
ROOT_URLCONF = 'cuddlybuddly.thumbnail.tests.urls'
MEDIA_ROOT = TEMP+'/cbttest'
MEDIA_URL = '/media/'
CUDDLYBUDDLY_THUMBNAIL_BASEDIR = 'basedir'
CUDDLYBUDDLY_THUMBNAIL_SUBDIR = 'subdir'
CUDDLYBUDDLY_THUMBNAIL_CACHE = TEMP+'/cbttest/cbttestcache'

try:
    from cuddlybuddly.thumbnail.tests3settings import *
except ImportError:
    pass

# Because PIL is crazy and I want to check my docstrings in admindocs
import PIL.Image
sys.modules['Image'] = PIL.Image
