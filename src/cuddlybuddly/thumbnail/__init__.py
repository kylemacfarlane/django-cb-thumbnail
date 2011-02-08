from cuddlybuddly.thumbnail.processors import CropToFitProcessor, \
    ResizeProcessor


LOADING = False
PROCESSORS = {
    'crop': CropToFitProcessor,
    'resize': ResizeProcessor
}
DEFAULT_PROCESSOR = ResizeProcessor


def register_processor(name, processor, default=False):
    global PROCESSORS
    PROCESSORS[name] = processor
    if default:
        global DEFAULT_PROCESSOR
        DEFAULT_PROCESSOR = processor


def get_processor(name):
    return PROCESSORS.get(name, DEFAULT_PROCESSOR)


def get_default_processor():
    return DEFAULT_PROCESSOR


def autodiscover():
    from django.conf import settings
    cache = getattr(settings, 'CUDDLYBUDDLY_THUMBNAIL_CACHE', None)
    if cache is None:
        return

    global LOADING
    if LOADING:
        return
    LOADING = True

    import imp
    from django.db.models import Model
    from django.db.models.base import ModelBase
    from django.db.models.fields.files import FieldFile
    from django.db.models.signals import post_save, pre_delete
    from django.utils.importlib import import_module
    from cuddlybuddly.thumbnail.listeners import update_cache

    for app in settings.INSTALLED_APPS:
        try:
            app_path = import_module(app).__path__
        except AttributeError:
            continue

        try:
            imp.find_module('models', app_path)
        except ImportError:
            continue

        models = import_module("%s.models" % app)
        for model in models.__dict__.values():
            if isinstance(model, ModelBase) and model is not Model:
                modelinit = model()
                for field in modelinit.__dict__.keys():
                    if isinstance(getattr(modelinit, field, None), FieldFile):
                        post_save.connect(update_cache, sender=model)
                        pre_delete.connect(update_cache, sender=model)
    LOADING = False
