import os
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
try:
    from PIL import Image
except ImportError:
    import Image
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models.loading import load_app
from django.template import Context, Template, TemplateSyntaxError
from django.test import TestCase
from django.utils.encoding import force_unicode, smart_str
from django.utils.hashcompat import md5_constructor
from cuddlybuddly import thumbnail
from cuddlybuddly.thumbnail import CropToFitProcessor, ResizeProcessor
from cuddlybuddly.thumbnail.exceptions import ThumbnailException
from cuddlybuddly.thumbnail.main import build_thumbnail_name, Thumbnail
from cuddlybuddly.thumbnail.tests.cbtfakeapp.models import FakeImage

try:
    set
except NameError:
    from sets import Set as set # For Python 2.3


RELATIVE_PIC_NAME = "cb-thumbnail-test.jpg"
PIC_NAME = RELATIVE_PIC_NAME
PIC_SIZE = (800, 600)
CACHE_DIR = os.path.join(settings.MEDIA_ROOT, 'cbttestcache')


class BaseTest(TestCase):
    def setUp(self):
        self.installed_apps = settings.INSTALLED_APPS
        settings.INSTALLED_APPS.append('cuddlybuddly.thumbnail.tests.cbtfakeapp')
        try:
            FakeImage.objects.count()
        except:
            load_app('cuddlybuddly.thumbnail.tests.cbtfakeapp')
            # Another try/except is needed because contrib.auth will sometimes
            # fail to create the permissions when some other third app is also
            # loaded.
            try:
                # Don't use call_command because if South is installed it
                # overrides syncdb and unnecessary warnings are printed out
                # during tests.
                from django.core.management.commands import syncdb
                syncdb.Command().handle_noargs(verbosity=0, interactive=False)
            except:
                pass

        self.images_to_delete = set()
        self.cache_to_delete = set()
        file = StringIO()
        Image.new('RGB', PIC_SIZE).save(file, 'JPEG')
        default_storage.save(PIC_NAME, ContentFile(file.getvalue()))
        self.images_to_delete.add(PIC_NAME)
        file.close()
        self.MEDIA_MIDDLE = os.path.join(
            getattr(settings, 'CUDDLYBUDDLY_THUMBNAIL_BASEDIR', ''),
            getattr(settings, 'CUDDLYBUDDLY_THUMBNAIL_SUBDIR', ''),
        )
        self.cache_backup = getattr(settings, 'CUDDLYBUDDLY_THUMBNAIL_CACHE', None)
        if not self.cache_backup:
            settings.CUDDLYBUDDLY_THUMBNAIL_CACHE = CACHE_DIR
        self.delete_cache_dir = False
        if self.cache_backup is None:
            if not os.path.exists(CACHE_DIR):
                self.delete_cache_dir = True
        cache = os.path.join(
            settings.CUDDLYBUDDLY_THUMBNAIL_CACHE,
            md5_constructor(smart_str(RELATIVE_PIC_NAME)).hexdigest()
        )
        self.cache_to_delete.add(cache)

        self.old_processors = thumbnail.PROCESSORS
        self.old_default_processor = thumbnail.DEFAULT_PROCESSOR
        thumbnail.PROCESSORS = {
            'crop': CropToFitProcessor,
            'resize': ResizeProcessor
        }
        thumbnail.DEFAULT_PROCESSOR = ResizeProcessor

    def verify_thumb(self, thumb, width, height, image):
        cache = os.path.join(
            self.MEDIA_MIDDLE,
            'cb-thumbnail-test_jpg_%s' % image
        )
        if isinstance(image, basestring):
            image = os.path.join(
                self.MEDIA_MIDDLE,
                'cb-thumbnail-test_jpg_%s' % image
            )
            thumb = force_unicode(thumb)
            self.assertEqual(
                os.path.normcase(thumb),
                os.path.normcase(image)
            )
            self.assert_(default_storage.exists(image),
                         'Does not exist: %s' % image)
            self.images_to_delete.add(image)
            file = default_storage.open(image, 'rb')
            imageobj = Image.open(ContentFile(file.read()))
            file.close()

            cache = os.path.join(
                settings.CUDDLYBUDDLY_THUMBNAIL_CACHE,
                md5_constructor(smart_str(cache)).hexdigest()
            )
            self.assert_(os.path.exists(cache), 'Does not exist: %s' % cache)
            self.cache_to_delete.add(cache)
        else:
            imageobj = Image.open(image)
        self.assertEqual(imageobj.size, (width, height))

    def render_template(self, source, context=None):
        if not context:
            context = {}
        context = Context(context)
        source = '{% load thumbnail_tags %}' + source
        return Template(source).render(context)

    def tearDown(self):
        settings.INSTALLED_APPS = self.installed_apps

        for image in self.images_to_delete:
            try:
                default_storage.delete(image)
            except:
                pass
        for image in self.cache_to_delete:
            try:
                os.remove(image)
            except:
                pass
        settings.CUDDLYBUDDLY_THUMBNAIL_CACHE = self.cache_backup
        if self.delete_cache_dir:
            try:
                os.rmdir(CACHE_DIR)
            except:
                pass

        thumbnail.PROCESSORS = self.old_processors
        thumbnail.DEFAULT_PROCESSOR = self.old_default_processor


class BuildThumbnailNameTests(TestCase):
    def setUp(self):
        self.settings_backup = {
            'CUDDLYBUDDLY_THUMBNAIL_BASEDIR':
                getattr(settings, 'CUDDLYBUDDLY_THUMBNAIL_BASEDIR', ''),
            'CUDDLYBUDDLY_THUMBNAIL_SUBDIR':
                getattr(settings, 'CUDDLYBUDDLY_THUMBNAIL_SUBDIR', ''),
        }

    def test_build(self):
        tests = (
            (('image.jpg', 50, 50), ['', ''], 'image_jpg_50x50_q85.jpg'),
            ([('media', 'image2.jpg'), 50, 80], ['base', 'sub'], 'image2_jpg_50x80_q85.jpg'),
            ([('media', 'test', 'image3.jpg'), 52, 50], ['', 's'], 'image3_jpg_52x50_q85.jpg'),
            (('/image4.png', 80, 70), ['b', ''], '/image4_png_80x70_q85.png'),
        )
        processor = ResizeProcessor()
        for test in tests:
            settings.CUDDLYBUDDLY_THUMBNAIL_BASEDIR = test[1][0]
            settings.CUDDLYBUDDLY_THUMBNAIL_SUBDIR = test[1][1]
            if hasattr(test[0][0], '__iter__'):
                test[0][0] = os.path.join(*test[0][0])
                test[1][0] = os.path.join(test[1][0], os.path.split(test[0][0])[0])

            args = list(test[0])
            args.append(processor)
            self.assertEqual(build_thumbnail_name(*args),
                             os.path.join(test[1][0], test[1][1], test[2]))

    def tearDown(self):
        for setting, value in self.settings_backup.iteritems():
            setattr(settings, setting, value)


class ThumbnailTests(BaseTest):
    def test_bad_init_values(self):
        self.assertRaises(ThumbnailException, Thumbnail, '', 'a', 1)
        self.assertRaises(ThumbnailException, Thumbnail, '', 1, 'a')
        self.assertRaises(ThumbnailException, Thumbnail, '', 1, 1, 'a')
        cache = os.path.join(
            settings.CUDDLYBUDDLY_THUMBNAIL_CACHE,
            md5_constructor(smart_str('')).hexdigest()
        )
        self.cache_to_delete.add(cache)

    def test_generate_from_string(self):
        thumb = Thumbnail(RELATIVE_PIC_NAME, 80, 60)
        self.verify_thumb(thumb, 80, 60, '80x60_q85.jpg')

    def test_generate_from_file_object(self):
        file = default_storage.open(PIC_NAME, 'rb')
        dest = os.path.join(
            self.MEDIA_MIDDLE,
            'cb-thumbnail-test_jpg_%s' % '40x30_q85.jpg'
        )
        thumb = Thumbnail(file, 40, 30, dest=dest)
        self.verify_thumb(thumb, 40, 30, '40x30_q85.jpg')
        cache = os.path.join(
            settings.CUDDLYBUDDLY_THUMBNAIL_CACHE,
            md5_constructor(force_unicode(file)).hexdigest()
        )
        self.cache_to_delete.add(cache)
        file.close()

    def test_generate_to_string(self):
        dest = os.path.join(self.MEDIA_MIDDLE,
                            'cb-thumbnail-test_jpg_string.jpg')
        thumb = Thumbnail(RELATIVE_PIC_NAME, 80, 60, dest=dest)
        self.verify_thumb(thumb, 80, 60, 'string.jpg')

    def test_generate_to_object(self):
        dest = StringIO()
        thumb = Thumbnail(RELATIVE_PIC_NAME, 80, 60, dest=dest)
        self.verify_thumb(thumb, 80, 60, dest)
        dest.close()

    def test_maintain_ratio(self):
        thumb = Thumbnail(RELATIVE_PIC_NAME, 80, 80)
        self.verify_thumb(thumb, 80, 60, '80x80_q85.jpg')

    def test_overwrites_existing(self):
        image = '8x6_q85.jpg'
        thumb = Thumbnail(RELATIVE_PIC_NAME, 8, 6)
        self.verify_thumb(thumb, 8, 6, image)
        thumb = Thumbnail(RELATIVE_PIC_NAME, 8, 6)
        self.verify_thumb(thumb, 8, 6, image)
        image = image.replace('.jpg', '_.jpg')
        image = os.path.join(
            self.MEDIA_MIDDLE,
            'cb-thumbnail-test_jpg_%s' % image
        )
        self.assert_(not default_storage.exists(image))
        cache = os.path.join(
            settings.CUDDLYBUDDLY_THUMBNAIL_CACHE,
            md5_constructor(smart_str(image)).hexdigest()
        )
        self.assert_(not os.path.exists(cache))

    def test_generate_to_unicode_filename(self):
        dest = os.path.join(self.MEDIA_MIDDLE,
                            u'cb-thumbnail-test_jpg_\u00E1\u00E9\u00ED\u00F3\u00FA.jpg')
        thumb = Thumbnail(RELATIVE_PIC_NAME, 80, 60, dest=dest)
        self.verify_thumb(thumb, 80, 60, u'\u00E1\u00E9\u00ED\u00F3\u00FA.jpg')

    def test_generate_from_unicode_filename(self):
        unicode_name = u'cb-thumbnail-test_jpg_\u00A3.jpg'
        file = default_storage.open(unicode_name, 'wb')
        Image.new('RGB', PIC_SIZE).save(file, 'JPEG')
        file.close()
        self.images_to_delete.add(unicode_name)
        cache = os.path.join(
            settings.CUDDLYBUDDLY_THUMBNAIL_CACHE,
            md5_constructor(smart_str(unicode_name)).hexdigest()
        )
        self.cache_to_delete.add(cache)
        thumb = Thumbnail(unicode_name, 80, 60)
        self.verify_thumb(thumb, 80, 60, u'\u00A3_jpg_80x60_q85.jpg')

    def test_generate_to_alternate_extension(self):
        dest = os.path.join(self.MEDIA_MIDDLE,
                            'cb-thumbnail-test_jpg_alt1.jpg')
        thumb = Thumbnail(RELATIVE_PIC_NAME, 80, 60, dest=dest)
        self.verify_thumb(thumb, 80, 60, 'alt1.jpg')
        dest2 = os.path.join(self.MEDIA_MIDDLE,
                            'cb-thumbnail-test_jpg_alt2.png')
        thumb = Thumbnail(RELATIVE_PIC_NAME, 80, 60, dest=dest2)
        self.verify_thumb(thumb, 80, 60, 'alt2.png')

        dest = default_storage.open(dest)
        dest2 = default_storage.open(dest2)
        self.assertNotEqual(dest.size, dest2.size)
        dest.close()
        dest2.close()

    def test_missing_source(self):
        self.assertRaises(ThumbnailException,
                          Thumbnail, RELATIVE_PIC_NAME+'missing', 80, 60)
        cache = os.path.join(
            settings.CUDDLYBUDDLY_THUMBNAIL_CACHE,
            md5_constructor(smart_str(RELATIVE_PIC_NAME+'missing')).hexdigest()
        )
        self.cache_to_delete.add(cache)

    def test_multiple_thumbs_from_single_source(self):
        source_cache = os.path.join(
            settings.CUDDLYBUDDLY_THUMBNAIL_CACHE,
            md5_constructor(smart_str(RELATIVE_PIC_NAME)).hexdigest()
        )
        self.assert_(not os.path.exists(source_cache))

        thumb1 = '8x6_q85.jpg'
        thumb1_cache = os.path.join(
            self.MEDIA_MIDDLE,
            'cb-thumbnail-test_jpg_%s' % thumb1
        )
        thumb1_cache = os.path.join(
            settings.CUDDLYBUDDLY_THUMBNAIL_CACHE,
            md5_constructor(smart_str(thumb1_cache)).hexdigest()
        )
        thumb = Thumbnail(RELATIVE_PIC_NAME, 8, 6)
        self.verify_thumb(thumb, 8, 6, thumb1)
        self.assert_(os.path.exists(source_cache))
        self.assert_(os.path.exists(thumb1_cache))
        source_cache_mtime1 = os.path.getmtime(source_cache)
        thumb1_cache_mtime = os.path.getmtime(thumb1_cache)

        thumb2 = '4x3_q85.jpg'
        thumb2_cache = os.path.join(
            self.MEDIA_MIDDLE,
            'cb-thumbnail-test_jpg_%s' % thumb2
        )
        thumb2_cache = os.path.join(
            settings.CUDDLYBUDDLY_THUMBNAIL_CACHE,
            md5_constructor(smart_str(thumb2_cache)).hexdigest()
        )
        thumb = Thumbnail(RELATIVE_PIC_NAME, 4, 3)
        self.verify_thumb(thumb, 4, 3, thumb2)
        self.assert_(os.path.exists(source_cache))
        self.assert_(os.path.exists(thumb1_cache))
        self.assert_(os.path.exists(thumb2_cache))
        source_cache_mtime2 = os.path.getmtime(source_cache)
        thumb2_cache_mtime = os.path.getmtime(thumb2_cache)

        self.assertEqual(source_cache_mtime1, source_cache_mtime2)
        self.assert_(source_cache_mtime1 <= thumb1_cache)
        self.assert_(source_cache_mtime2 <= thumb2_cache)


class TemplateTests(BaseTest):
    def test_bad_values(self):
        tests = (
            '{% thumbnail %}',
            '{% thumbnail "a" %}',
            '{% thumbnail "a" 1 %}',
            '{% thumbnail "a" as %}',
            '{% thumbnail "a" 80 60 as %}',
            '{% thumbnail "a" width=80 60 %}',
        )
        for test in tests:
            self.assertRaises(TemplateSyntaxError, self.render_template, test)

    def test_good_values(self):
        image = FakeImage(image=RELATIVE_PIC_NAME, misc=1)
        image.save()

        basedir = getattr(settings, 'CUDDLYBUDDLY_THUMBNAIL_BASEDIR', '')
        subdir = getattr(settings, 'CUDDLYBUDDLY_THUMBNAIL_SUBDIR', '')
        tests = {
            '{% thumbnail "'+RELATIVE_PIC_NAME+'" 51 51 %}':
                ((basedir, subdir), 'cb-thumbnail-test_jpg_51x51_q85.jpg'),
            '{% thumbnail "'+RELATIVE_PIC_NAME+'" 52 52 %}':
                ((basedir, subdir), 'cb-thumbnail-test_jpg_52x52_q85.jpg'),
            '{% thumbnail "'+RELATIVE_PIC_NAME+'" 53 53 as thumb %}{{ thumb }}':
                ((basedir, subdir), 'cb-thumbnail-test_jpg_53x53_q85.jpg'),
            '{% thumbnail "'+RELATIVE_PIC_NAME+'" 54 54 "cb-thumbnail-test_jpg_tag.jpg" %}':
                ('', 'cb-thumbnail-test_jpg_tag.jpg'),
            '{% thumbnail "'+RELATIVE_PIC_NAME+'" 54 54 "cb-thumbnail-test_jpg_tag2.jpg" %}':
                ('', 'cb-thumbnail-test_jpg_tag2.jpg'),
            '{% thumbnail source width height dest as thumb %}{{ thumb }}':
                ('', 'cb-thumbnail-test_jpg_templatevars.jpg', {
                    'source': RELATIVE_PIC_NAME,
                    'width': 66,
                    'height': 77,
                    'dest': 'cb-thumbnail-test_jpg_templatevars.jpg'
                }),
            '{% thumbnail source.image width height dest as thumb %}{{ thumb }}':
                ('', 'cb-thumbnail-test_jpg_field.jpg', {
                    'source': image,
                    'width': 67,
                    'height': 78,
                    'dest': 'cb-thumbnail-test_jpg_field.jpg'
                }),
            '{% thumbnail source width height=height dest=dest as thumb %}{{ thumb }}':
                ('', 'cb-thumbnail-test_jpg_templatevars2.jpg', {
                    'source': RELATIVE_PIC_NAME,
                    'width': 66,
                    'height': 77,
                    'dest': 'cb-thumbnail-test_jpg_templatevars2.jpg'
                }),
            '{% thumbnail "'+RELATIVE_PIC_NAME+'" 60 60 quality=75 as thumb %}{{ thumb }}':
                ((basedir, subdir), 'cb-thumbnail-test_jpg_60x60_q75.jpg'),
            '{% thumbnail "'+RELATIVE_PIC_NAME+'" 60 60 None None quality=50 as thumb %}{{ thumb }}':
                ((basedir, subdir), 'cb-thumbnail-test_jpg_60x60_q50.jpg'),
            '{% thumbnail "'+RELATIVE_PIC_NAME+'" 60 60 upscale=1 as thumb %}{{ thumb }}':
                ((basedir, subdir), 'cb-thumbnail-test_jpg_60x60_q85_up.jpg'),
            '{% thumbnail "'+RELATIVE_PIC_NAME+'" 60 60 upscale=1 unused=2 as thumb %}{{ thumb }}':
                ((basedir, subdir), 'cb-thumbnail-test_jpg_60x60_q85_up.jpg'),
            '{% thumbnail "'+RELATIVE_PIC_NAME+'" 60 60 upscale=0 as thumb %}{{ thumb }}':
                ((basedir, subdir), 'cb-thumbnail-test_jpg_60x60_q85.jpg'),
            '{% thumbnail "'+RELATIVE_PIC_NAME+'" 60 60 upscale=1 quality=50 as thumb %}{{ thumb }}':
                ((basedir, subdir), 'cb-thumbnail-test_jpg_60x60_q50_up.jpg'),
            '{% thumbnail "'+RELATIVE_PIC_NAME+'" 50 50 proc=\'crop\' quality=50 as thumb %}{{ thumb }}':
                ((basedir, subdir), 'cb-thumbnail-test_jpg_50x50_q50_ctf.jpg'),
        }
        for name, val in tests.items():
            if len(val) == 2:
                val = (val[0], val[1], {})
            if hasattr(val[0], '__iter__'):
                path = os.path.join(*val[0])
            else:
                path = val[0]
            path = os.path.join(path, val[1])
            cache = os.path.join(
                settings.CUDDLYBUDDLY_THUMBNAIL_CACHE,
                md5_constructor(smart_str(path)).hexdigest()
            )
            self.cache_to_delete.add(cache)
            path = path.replace('\\', '/')
            self.assertEqual(self.render_template(name, val[2]), path)
            self.assert_(default_storage.exists(path))
            self.images_to_delete.add(path)
        image.delete()

    def test_silent_failure(self):
        tests = {
            '{% thumbnail "'+RELATIVE_PIC_NAME+'missing" 51 51 %}': '',
            '{% thumbnail "'+RELATIVE_PIC_NAME+'" "a" 51 %}': '',
        }
        for name, val in tests.items():
            if type(val).__name__ == 'str':
                val = (val, None)
            self.assertEqual(self.render_template(name, val[1]), val[0])
        cache = os.path.join(
            settings.CUDDLYBUDDLY_THUMBNAIL_CACHE,
            md5_constructor(smart_str(RELATIVE_PIC_NAME+'missing')).hexdigest()
        )
        self.cache_to_delete.add(cache)


class ModelsTests(BaseTest):
    def test_autodiscover(self):
        thumbnail.autodiscover()
        image = FakeImage(image=RELATIVE_PIC_NAME, misc=1)
        image.save()

        thumb = Thumbnail(image.image, 20, 15)
        self.verify_thumb(thumb, 20, 15, '20x15_q85.jpg')
        cache = os.path.join(
            settings.CUDDLYBUDDLY_THUMBNAIL_CACHE,
            md5_constructor(force_unicode(image.image)).hexdigest()
        )
        self.assert_(os.path.exists(cache), 'Does not exist: %s' % cache)
        self.cache_to_delete.add(cache)

        image.misc = 1
        image.save()
        self.assert_(not os.path.exists(cache), 'Should not exist: %s' % cache)

        thumb = Thumbnail(image.image, 20, 15)
        self.verify_thumb(thumb, 20, 15, '20x15_q85.jpg')
        self.assert_(os.path.exists(cache), 'Does not exist: %s' % cache)

        image.delete()
        self.assert_(not os.path.exists(cache), 'Should not exist: %s' % cache)


class ProcessorRegistryTests(BaseTest):
    def test_processor_registry(self):
        self.assertEqual(thumbnail.get_processor('resize'), ResizeProcessor)
        self.assertEqual(thumbnail.get_processor('crop'), CropToFitProcessor)
        self.assertEqual(thumbnail.get_default_processor(), ResizeProcessor)
        self.assertEqual(thumbnail.get_processor('bad'), ResizeProcessor)

        thumbnail.register_processor('whatever', ResizeProcessor)
        self.assertEqual(thumbnail.get_processor('whatever'), ResizeProcessor)

        thumbnail.register_processor('crop', CropToFitProcessor, default=True)
        self.assertEqual(thumbnail.get_default_processor(), CropToFitProcessor)
        self.assertEqual(thumbnail.get_processor('bad'), CropToFitProcessor)


class ResizeProcessorTests(BaseTest):
    def test_generate_filename(self):
        tests = (
            ((85, False), ('testing.jpg', 50, 50), 'testing_jpg_50x50_q85.jpg'),
            ((85, False), ('testing.png', 50, 50), 'testing_png_50x50_q85.png'),
            ((75, True), ('testing.jpg', 75, 75), 'testing_jpg_75x75_q75_up.jpg')
        )
        for test in tests:
            proc = ResizeProcessor(quality=test[0][0], upscale=test[0][1])
            self.assertEqual(proc.generate_filename(*test[1]), test[2])

    def test_generate_thumbnail(self):
        image = Image.new('RGB', PIC_SIZE)
        tests = (
            (False, (400, 300), (400, 300)),
            (False, (400, 400), (400, 300)),
            (True, (1600, 1200), (1600, 1200)),
        )
        for test in tests:
            proc = ResizeProcessor(upscale=test[0])
            thumb = proc.generate_thumbnail(image, *test[1])
            self.assertEqual(thumb.size, test[2])


class CropToFitProcessorTests(BaseTest):
    def test_generate_filename(self):
        tests = (
            ((85, False), ('testing.jpg', 50, 50), 'testing_jpg_50x50_q85_ctf.jpg'),
            ((85, False), ('testing.png', 50, 50), 'testing_png_50x50_q85_ctf.png'),
            ((75, True), ('testing.jpg', 75, 75), 'testing_jpg_75x75_q75_up_ctf.jpg')
        )
        for test in tests:
            proc = CropToFitProcessor(quality=test[0][0], upscale=test[0][1])
            self.assertEqual(proc.generate_filename(*test[1]), test[2])

    def test_generate_thumbnail(self):
        image = Image.new('RGB', PIC_SIZE)
        tests = (
            (False, (400, 300), (400, 300)),
            (False, (400, 400), (400, 400)),
            (True, (1600, 1200), (1600, 1200)),
        )
        for test in tests:
            proc = CropToFitProcessor(upscale=test[0])
            thumb = proc.generate_thumbnail(image, *test[1])
            self.assertEqual(thumb.size, test[2])
