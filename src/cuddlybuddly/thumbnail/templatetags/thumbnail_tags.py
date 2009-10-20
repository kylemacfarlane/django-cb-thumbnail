import os
from django import template
from django.conf import settings
from django.utils.encoding import force_unicode, iri_to_uri
from cuddlybuddly.thumbnail.main import Thumbnail


register = template.Library()


class ThumbnailNode(template.Node):
    def __init__(self, source, width, height, quality=None, dest=None,
                 as_var=None):
        self.source = template.Variable(source)
        self.width = template.Variable(width)
        self.height = template.Variable(height)
        if quality is not None and quality != 'None':
            self.quality = template.Variable(quality)
        else:
            self.quality = None
        if dest is not None:
            self.dest = template.Variable(dest)
        else:
            self.dest = None
        self.as_var = as_var

    def render(self, context):
        vars = {
            'source': self.source.resolve(context),
            'width': self.width.resolve(context),
            'height': self.height.resolve(context)
        }
        if self.quality is not None:
            vars['quality'] = self.quality.resolve(context)
        if self.dest is not None:
            vars['dest'] = self.dest.resolve(context)
        try:
            thumb = Thumbnail(**vars)
        except:
            if settings.DEBUG:
                raise
            else:
                thumb = ''
        else:
            thumb = force_unicode(thumb).replace(settings.MEDIA_ROOT, '')
            thumb = iri_to_uri('/'.join(thumb.strip('\\/').split(os.sep)))
        if self.as_var:
            context[self.as_var] = thumb
            return ''
        else:
            return thumb


def do_thumbnail(parser, token):
    """
    Creates a thumbnail if needed and displays its url.

    Usage::

        {% thumbnail source width height [quality] [destination] %}

    Source and destination can be a file like object or a string to a path.
    """

    split_token = token.split_contents()
    vars = []
    as_var = False
    for k, v in enumerate(split_token[1:]):
        if v == 'as':
            try:
                while len(vars) < 5:
                    vars.append(None)
                vars.append(split_token[k+2])
                as_var = True
            except IndexError:
                raise template.TemplateSyntaxError, \
                      "%r tag requires a variable name to attach to" \
                      % split_token[0]
            break
        else:
            vars.append(v)

    if (not as_var and len(vars) not in (3, 4, 5)) \
       or (as_var and len(vars) not in (4, 5, 6)):
        raise template.TemplateSyntaxError, \
              "%r tag requires a source, a width and a height" \
              % token.contents.split()[0]

    return ThumbnailNode(*vars)


do_thumbnail = register.tag('thumbnail', do_thumbnail)
