import hashlib
import os
from django.conf import settings
from django.db.models.fields.files import FieldFile
from django.utils.encoding import force_unicode


def update_cache(sender, instance, **kwargs):
    for field in instance.__dict__.keys():
        field = getattr(instance, field)
        if isinstance(field, FieldFile):
            cache_dir = getattr(settings, 'CUDDLYBUDDLY_THUMBNAIL_CACHE', None)
            field = force_unicode(field)
            if field and cache_dir is not None:
                cache = os.path.join(
                    cache_dir,
                    hashlib.md5(field).hexdigest()
                )
                if os.path.exists(cache):
                    os.remove(cache)
