import hashlib
import os
import pickle
try:
    from PIL import Image
except ImportError:
    import Image
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from django.conf import settings
from django.core.files.base import ContentFile, File
from django.core.files.storage import default_storage
from django.db.models.fields.files import FieldFile
from django.utils.encoding import force_unicode, smart_str
from cuddlybuddly.thumbnail import get_processor
from cuddlybuddly.thumbnail.exceptions import ThumbnailException


def build_thumbnail_name(source, width, height, processor):
    source = force_unicode(source)
    path, filename = os.path.split(source)
    filename = processor.generate_filename(filename, width, height)
    return os.path.join(
        getattr(settings, 'CUDDLYBUDDLY_THUMBNAIL_BASEDIR', ''),
        path,
        getattr(settings, 'CUDDLYBUDDLY_THUMBNAIL_SUBDIR', ''),
        filename
    )


class Thumbnail(object):
    def __init__(self, source, width, height, dest=None, proc=None, *args,
                 **kwargs):
        self.source = source
        self.width = width
        self.height = height
        self.processor = get_processor(proc)(*args, **kwargs)
        if dest is None:
            dest = build_thumbnail_name(source, width, height, self.processor)
        self.dest = dest
        self.cache_dir = getattr(settings, 'CUDDLYBUDDLY_THUMBNAIL_CACHE', None)

        for var in ('width', 'height'):
            try:
                setattr(self, var, int(getattr(self, var)))
            except ValueError:
                raise ThumbnailException('Value supplied for \'%s\' is not an int' % var)
        if self.processor is None:
            raise ThumbnailException('There is no image processor available')

        self.generate()

    def __unicode__(self):
        return force_unicode(self.dest)

    def generate(self):
        if hasattr(self.dest, 'write'):
            self._do_generate()
        else:
            do_generate = False
            if self.cache_dir is not None:
                if isinstance(self.source, FieldFile) or \
                   isinstance(self.source, File):
                    source = force_unicode(self.source)
                elif not isinstance(self.source, basestring):
                    source = pickle.dumps(self.source.read())
                    self.source.seek(0)
                else:
                    source = smart_str(force_unicode(self.source))
                source = os.path.join(self.cache_dir,
                                      hashlib.md5(source).hexdigest())
                if not os.path.exists(source):
                    path = os.path.split(source)[0]
                    if not os.path.exists(path):
                        os.makedirs(path)
                    open(source, 'w').close()
                if not isinstance(self.dest, basestring):
                    dest = pickle.dumps(self.dest.read())
                    self.dest.seek(0)
                else:
                    dest = smart_str(force_unicode(self.dest))
                dest = os.path.join(self.cache_dir,
                                      hashlib.md5(dest).hexdigest())
            else:
                source = force_unicode(self.source)
                dest = self.dest

            if hasattr(default_storage, 'modified_time') and not self.cache_dir:
                try:
                    source_mod_time = default_storage.modified_time(source)
                except EnvironmentError:
                    # Means the source file doesn't exist, so nothing can be
                    # done.
                    do_generate = False
                else:
                    try:
                        dest_mod_time = default_storage.modified_time(dest)
                    except EnvironmentError:
                        # Means the destination file doesn't exist so it must be
                        # generated.
                        do_generate = True
                    else:
                        do_generate = source_mod_time > dest_mod_time
            else:
                if not self.cache_dir:
                    source_cache = os.path.join(settings.MEDIA_ROOT, source)
                    dest_cache = os.path.join(settings.MEDIA_ROOT, dest)
                else:
                    source_cache, dest_cache = source, dest
                try:
                    do_generate = os.path.getmtime(source_cache) > \
                            os.path.getmtime(dest_cache)
                except OSError:
                    do_generate = True

            if do_generate:
                if self.cache_dir is not None:
                    path = os.path.split(dest)[0]
                    if not os.path.exists(path):
                        os.makedirs(path)
                    open(dest, 'w').close()
                try:
                    self._do_generate()
                except:
                    if self.cache_dir is not None:
                        if os.path.exists(dest):
                            os.remove(dest)
                    raise

    def _do_generate(self):
        if isinstance(self.source, Image.Image):
            data = self.source
        else:
            try:
                if not hasattr(self.source, 'readline'):
                    if not hasattr(self.source, 'read'):
                        source = force_unicode(self.source)
                        if not default_storage.exists(source):
                            raise ThumbnailException('Source does not exist: %s'
                                                     % self.source)
                        file = default_storage.open(source, 'rb')
                        content = ContentFile(file.read())
                        file.close()
                    else:
                        content = ContentFile(self.source.read())
                else:
                    content = ContentFile(self.source.read())
                data = Image.open(content)
            except IOError, detail:
                raise ThumbnailException('%s: %s' % (detail, self.source))
            except MemoryError:
                raise ThumbnailException('Memory Error: %s' % self.source)

        filelike = hasattr(self.dest, 'write')
        if not filelike:
            dest = StringIO()
        else:
            dest = self.dest

        data = self.processor.generate_thumbnail(data, self.width, self.height)

        filename = force_unicode(self.dest)
        try:
            data.save(dest, optimize=1, **self.processor.get_save_options(filename, data))
        except IOError:
            # Try again, without optimization (PIL can't optimize an image
            # larger than ImageFile.MAXBLOCK, which is 64k by default)
            try:
                data.save(dest, **self.processor.get_save_options(filename, data))
            except IOError, e:
                raise ThumbnailException(e)

        if hasattr(self.source, 'seek'):
            self.source.seek(0)
        if filelike:
            dest.seek(0)
        else:
            if default_storage.exists(filename):
                default_storage.delete(filename)
            default_storage.save(filename, ContentFile(dest.getvalue()))
            dest.close()
