=============================
django-cuddlybuddly-thumbnail
=============================

A Django app that supplies a template tag to generate thumbnails. Specifically designed to be compatible with properly implemented Django storage systems, which unfortunately most are not. Look for ``django-cuddlybuddly-storage-s3`` for a fully working Amazon S3 storage system.

The actual image processing is mostly from ``sorl-thumbnail``.


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

An optional location on your local disk to store a cache to increase performance when using remote storage systems.

``CUDDLYBUDDLY_THUMBNAIL_BASEDIR``
----------------------------------

Save thumbnail images to a directory directly off ``MEDIA_ROOT``, still keeping the relative directory structure of the source image.

    CUDDLYBUDDLY_THUMBNAIL_BASEDIR = '_thumbs' 

Results in:

    MEDIA_ROOT + 'thumbs/photos/1_jpg_150x150_q85.jpg'


``CUDDLYBUDDLY_THUMBNAIL_SUBDIR``
---------------------------------

Save thumbnail images to a sub-directory relative to the source image.

    CUDDLYBUDDLY_THUMBNAIL_SUBDIR = '_thumbs'

Results in:

    MEDIA_ROOT + 'photos/_thumbs/1_jpg_150x150_q85.jpg'


Template Tag
============

``thumbnail``
-------------

Creates a thumbnail and returns its relative path without the ``MEDIA_URL`` attached.

Usage::

    {% thumbnail source width height %}
    {% thumbnail source width height as var %}
    {% thumbnail source width height quality %}
    {% thumbnail source width height quality as var %}
    {% thumbnail source width height quality destination %}
    {% thumbnail source width height quality destination as var %}

Usually it will just be something like::

    <img src="{{ MEDIA_URL }}{% thumbnail source width height %}" alt="" />


``source`` and ``destination`` can be paths as strings or file like objects. ``width``, ``height`` and ``quality`` must all be integers. ``quality`` must be between ``1`` and ``100`` and defaults to ``85``. ``destination`` by default is calculated using your directory settings and the properties of the thumbnail itself.
