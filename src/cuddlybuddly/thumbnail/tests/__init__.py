from django.conf import settings


if not getattr(settings, 'CUDDLYBUDDLY_THUMBNAIL_SKIP_TESTS', False):
    from cuddlybuddly.thumbnail.tests.tests import *
