from itertools import tee

from django import template
from memoize import memoize

register = template.Library()


@register.tag
@memoize(3600)
def is_system_initialized():
    from ..models import GeneralSetup
    return GeneralSetup.objects.exists()


@register.filter
def get_py_value(func_name, argskwargs=None):
    argskwargs = argskwargs.split(',') if argskwargs else ()
    it1, it2 = tee(argskwargs)
    args, kwargs = filter(lambda x: '=' not in x, it1), filter(lambda x: '=' in x, it2)
    return register.tags[func_name](*args, **dict(item.split('=') for item in kwargs))
