import os
try:
    from PIL import Image, ImageOps
except ImportError:
    import Image, ImageOps


class BaseProcessor(object):
    # PIL defaults to 75 but since we've been using 85 since sorl-thumbnail we
    # should keep it at 85 to prevent mass regeneration of thumbnails.
    quality = 85

    def __init__(self, *args, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)

    def generate_filename(self, filename, width, height):
        """
        Generate the thumbnail's filename from the filename of the source image.
        It should be unique and take into account the processor, dimensions and
        any specific settings.

        The supplied filename does not include the path and neither should the
        returned filename.
        """
        raise NotImplementedError()

    def generate_thumbnail(self, image, width, height):
        """
        Generate the thumbnail from the source image. Image will be an instance
        of Image.Image from PIL and this method should also return an instance
        of Image.Image, which should make most processors chainable.
        """
        raise NotImplementedError()

    def get_save_options(self, filename, image):
        """
        Return the options for Image's save() method. The available options vary
        depending on the image format but PIL silently ignores unused options
        (the docs for save() say they're ignored but in practice that doesn't
        seem to be true). Format must always be returned.

        "Image File Formats" under "Appendixes" at
        http://www.pythonware.com/library/pil/handbook/index.htm lists the
        available options.
        """

        format = Image.EXTENSION.get(
            os.path.splitext(filename)[1].lower(), 'JPEG'
        )
        options = {
            'format': format,
            'quality': self.quality,
        }
        if format == 'GIF' or (format == 'PNG' and image.mode in ('L', 'P')):
            transparency = image.info.get('transparency')
            if transparency:
                options['transparency'] = transparency
        return options

    def _colorspace(self, im, bw=False, replace_alpha=False):
        """
        A utility method taken from SmileyChris' easy-thumbnails that a lot of
        processors will probably want to use.

        Convert images to the correct color space.

        A passive option (i.e. always processed) of this method is that all images
        (unless grayscale) are converted to RGB colorspace.

        This processor should be listed before :func:`scale_and_crop` so palette is
        changed before the image is resized.

        bw
            Make the thumbnail grayscale (not really just black & white).

        replace_alpha
            Replace any transparency layer with a solid color. For example,
            ``replace_alpha='#fff'`` would replace the transparency layer with
            white.

        """
        if bw and im.mode != 'L':
            return im.convert('L')

        if im.mode in ('L', 'RGB'):
            return im

        if im.mode == 'RGBA' or (im.mode == 'P' and 'transparency' in im.info):
            if im.mode != 'RGBA':
                im = im.convert('RGBA')
            if not replace_alpha:
                return im
            base = Image.new('RGBA', im.size, replace_alpha)
            base.paste(im)
            im = base

        return im.convert('RGB')


class ResizeProcessor(BaseProcessor):
    """
    A processor to maintain the aspect ratio and resizes so that the smaller
    side matches the specified dimensions, e.g. a 150x100 image resized to 50x50
    will end up as 75x50.
    """

    upscale = False

    def generate_filename(self, filename, width, height):
        """
        This method breaks convention by not somehow including the name of the
        processor in the filename, but doing so at this point would be backwards
        incompatible and cause mass regeneration of thumbnails.
        """
        basename, ext = os.path.splitext(filename)
        name = '%s%s' % (basename, ext.replace(os.extsep, '_'))
        upscale = '_up' if self.upscale else ''
        return '%s_%sx%s_q%s%s%s' % (name, width, height, self.quality, upscale,
                                     ext)

    def generate_thumbnail(self, image, width, height):
        image = self._colorspace(image)
        source_x, source_y = [float(v) for v in image.size]
        target_x, target_y = [float(v) for v in (width, height)]
        scale = min(target_x / source_x, target_y / source_y)
        if scale < 1.0 or (scale > 1.0 and self.upscale):
            # There's also image.thumbnail which is meant to be faster but lower
            # quality.
            image = image.resize(
                (int(round(source_x * scale)), int(round(source_y * scale))),
                resample=Image.ANTIALIAS
            )
        image = self._colorspace(image)
        return image


class CropToFitProcessor(ResizeProcessor):
    """
    A processor to maintain the aspect ratio and resizes so that the smaller
    side matches the specified dimensions and then crops out the excess, e.g. a
    150x100 image resized to 50x50 will end up as 50x50 with the left and right
    cropped off.
    """
    def generate_filename(self, *args, **kwargs):
        filename = super(CropToFitProcessor, self).generate_filename(
            *args, **kwargs
        )
        basename, ext = os.path.splitext(filename)
        return '%s_ctf%s' % (basename, ext)

    def generate_thumbnail(self, image, width, height):
        image = super(CropToFitProcessor, self).generate_thumbnail(
            image, width, height
        )
        return ImageOps.fit(image, (width, height), Image.ANTIALIAS)
