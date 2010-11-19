import os
from django import template
from django.conf import settings
from django.template.defaulttags import kwarg_re
from django.utils.encoding import force_unicode, iri_to_uri
from cuddlybuddly.thumbnail.main import Thumbnail


register = template.Library()


class ThumbnailNode(template.Node):
    def __init__(self, source, width, height, dest=None, proc=None,
                 as_var=None, extra_args=[], **kwargs):
        self.image_source = template.Variable(source)
        self.width = template.Variable(width)
        self.height = template.Variable(height)
        if dest is not None and dest != 'None':
            self.dest = template.Variable(dest)
        else:
            self.dest = None
        if proc is not None and proc != 'None':
            self.proc = template.Variable(proc)
        else:
            self.proc = None
        self.as_var = as_var
        self.extra_args = [template.Variable(x) for x in extra_args]
        self.extra_kwargs = dict(
            [(k, template.Variable(v)) for k, v in kwargs.items()]
        )

    def render(self, context):
        args = [
            self.image_source.resolve(context),
            self.width.resolve(context),
            self.height.resolve(context)
        ]
        if self.dest is not None:
            args.append(self.dest.resolve(context))
        else:
            args.append(None)
        if self.proc is not None:
            args.append(self.proc.resolve(context))
        else:
            args.append(None)
        for arg in self.extra_args:
            args.append(arg.resolve(context))
        kwargs = dict(
            [(k, v.resolve(context)) for k, v in self.extra_kwargs.items()]
        )
        try:
            thumb = Thumbnail(*args, **kwargs)
        except:
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

        {% thumbnail source width height [destination] [processor] %}

    Or with keyword arguments::

        {% thumbnail source width height desc=destination proc=processor %}

    Keyword arguments specifying a processor and some custom options for it::

        {% thumbnail source width height proc=custom option1=var option2='str' %}

    Source and destination can be a file like object or a path as a string.
    """

    split_token = token.split_contents()
    args = []
    kwargs = {}
    as_var = None
    started_kwargs = False
    for k, v in enumerate(split_token[1:]):
        if v == 'as':
            try:
                as_var = split_token[k+2]
            except IndexError:
                raise template.TemplateSyntaxError(
                    "%r tag requires a variable name to attach to" \
                    % split_token[0]
                )
            break
        else:
            match = kwarg_re.match(v)
            if not match:
                raise template.TemplateSyntaxError(
                    "Malformed arguments to %r tag" % split_token[0]
                )
            name, value = match.groups()
            if name:
                kwargs[name] = value
                started_kwargs = True
            else:
                if started_kwargs:
                    raise template.TemplateSyntaxError(
                        "Positional arguments cannot come after keyword arguments"
                    )
                args.append(value)
    kwargs['as_var'] = as_var

    required_args = ['height', 'width', 'source']
    for i in range(0, len(args)):
        if required_args:
            required_args.pop()
    for arg in required_args:
        if arg not in kwargs:
            raise template.TemplateSyntaxError(
                "%r tag requires a source, a width and a height" \
                % split_token[0]
            )

    if len(args) > 5:
        kwargs['extra_args'] = args[5:]
        args = args[0:5]
    return ThumbnailNode(*args, **kwargs)


do_thumbnail = register.tag('thumbnail', do_thumbnail)
