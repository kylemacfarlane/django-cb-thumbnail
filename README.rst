=============================
django-cuddlybuddly-thumbnail
=============================

A Django app that supplies a template tag to generate thumbnails. Specifically designed to be compatible with properly implemented Django storage systems, which unfortunately most are not. Look for ``django-cuddlybuddly-storage-s3`` for a fully working Amazon S3 storage system.


Installation
============

1. Add ``cuddlybuddly.thumbnail`` to your ``INSTALLED_APPS``.
2. If using a remote storage system, set ``CUDDLYBUDDLY_THUMBNAIL_CACHE`` to a location on the local disk to store a local cache of hashes to increase access times.
3. If using a remote storage system and have setup the local cache, add the following to your URLconf to automatically attach signals to all models with a file field that may need to be cached::

    from cuddlybuddly import thumbnail
    thumbnail.autodiscover()

4. Add ``{% load thumbnail_tags %}`` to the templates where you wish to use the template tag.


Settings
========

``CUDDLYBUDDLY_THUMBNAIL_CACHE``
--------------------------------

An optional location on your local disk to store a cache to increase performance when using remote storage systems. Do not use this if your remote storage system has its own cache as this feature is basically just a mass of signals that could go wrong. For example, ``django-cuddlybuddly-storage-s3`` has its own proper cache at the storage level.

``CUDDLYBUDDLY_THUMBNAIL_BASEDIR``
----------------------------------

Save thumbnail images to a directory directly off ``MEDIA_ROOT``, still keeping the relative directory structure of the source image.

    CUDDLYBUDDLY_THUMBNAIL_BASEDIR = '_thumbs' 

Results in:

    MEDIA_ROOT + '_thumbs/photos/1_jpg_150x150_q85.jpg'


``CUDDLYBUDDLY_THUMBNAIL_SUBDIR``
---------------------------------

Save thumbnail images to a sub-directory relative to the source image.

    CUDDLYBUDDLY_THUMBNAIL_SUBDIR = '_thumbs'

Results in:

    MEDIA_ROOT + 'photos/_thumbs/1_jpg_150x150_q85.jpg'


``CUDDLYBUDDLY_THUMBNAIL_SKIP_TESTS``
-------------------------------------

Optional and defaults to false. Set to a true value to skip the tests as they can be pretty slow when using a remote storage backend.


Template Tag
============

``thumbnail``
-------------

Creates a thumbnail and returns its relative path without the ``MEDIA_URL`` attached.

Usage::

    {% thumbnail source width height %}
    {% thumbnail source width height as var %}
    {% thumbnail source width height destination %}
    {% thumbnail source width height destination as var %}
    {% thumbnail source width height destination processor %}
    {% thumbnail source width height destination processor as var %}


Or by using keyword arguments. Notice how extra options can be specified for the processor by using keyword arguments at the end::

    {% thumbnail source width height dest='/media/test.jpg' proc='crop' upscale=1 quality=50 %}
    {% thumbnail source width height=height proc='crop' quality=50 as var %}


Usually it will just be something like::

    <img src="{{ MEDIA_URL }}{% thumbnail source width height %}" alt="" />


``source`` and ``destination`` can be paths as strings or file like objects. ``width`` and ``height`` must be integers. ``processor`` is the string name of the image processor you want to use. ``destination`` by default is calculated using your directory settings and the properties of the thumbnail itself. If an unknown or no processor is specified then the default will be used.


Image Processors
================

Rather than endlessly adding requested features this app uses easily pluggable image processors to generate thumbnails (doesn't have to be thumbnails).

``ResizeProcessor``
-------------------

This processor merely resizes the image so that the smallest side matches the requested dimensions, e.g. a 150x100 image resized to 50x50 will end up as 75x50. By default this is registered as ``resize`` and is the default processor. It has two options; ``quality`` which defualts to ``85`` and ``upscale`` which defaults to ``False``. If ``upscale`` is set to ``True`` then images smaller than the requested dimensions will be upscaled, e.g. a 25x25 image resized to 50x50 will come out as 50x50 instead of being left alone.

``CropToFitProcessor``
----------------------

This processor is the same as ``ResizeProcessor`` except that it will crop the image if necessary to match the requested dimensions, e.g. a 150x100 image resized to 50x50 will end up as 50x50 with the left and right cropped off. By default it is registered as ``crop`` and has the same options as ``ResizeProcessor``.


Custom Image Processors
=======================

To create image processors you just need to extend ``cuddlybuddly.thumbnail.processors.BaseProcessor``, implement ``generate_filename`` and ``generate_thumbnail`` and then register the processor in your project's urls.py.

The following is a very simple example of creating a processor that merely changes the default quality of ``ResizeProcessor``. Put this in a project's urls.py::

    from cuddlybuddly import thumbnail
    from cuddlybuddly.thumbnail.processors import ResizeProcessor

    class MyProcessor(ResizeProcessor):
        quality = 50

    thumbnail.register_processor('myprocessor', MyProcessor)


Now you can use your processor with the template tag::

    {% thumbnail source width height proc='myprocessor' %}


Or we could have registered it as the new default processor by instead having the following in urls.py::

    thumbnail.register_processor('myprocessor', MyProcessor, default=True)


Now we can use it with the template tag without having to specify a processor::

    {% thumbnail source width height %}


Processor Options
-----------------

Any unused arguments from the ``thumbnail`` template tag are passed along to image processors and so you can use them to specify extra options. Take the following example::

    class MyProcessor(BaseProcessor):
        my_option = 50

        def generate_thumbnail(self, image, width, height):
            print self.my_option


Now ``my_option`` will default to ``50`` but we can set it to something else from the template tag::

    {% thumbnail source width height my_option=75 %}


