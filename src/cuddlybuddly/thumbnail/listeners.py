import os
from django.conf import settings
from django.db.models.fields.files import FieldFile
from django.utils.encoding import force_unicode
from django.utils.hashcompat import md5_constructor


def update_cache(sender, instance, **kwargs):
    for field in instance.__dict__.keys():
        field = getattr(instance, field)
        if isinstance(field, FieldFile):
            cache_dir = getattr(settings, 'CUDDLYBUDDLY_THUMBNAIL_CACHE', '')
            field = force_unicode(field)
            if field:
                cache = os.path.join(
                    cache_dir,
                    md5_constructor(field).hexdigest()
                )
                if os.path.exists(cache):
                    os.remove(cache)
