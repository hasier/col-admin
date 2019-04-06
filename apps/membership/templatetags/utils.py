from django import template
from memoize import memoize

register = template.Library()


@register.simple_tag
@memoize(3600)
def is_system_initialized():
    from ..models import GeneralSetup
    return GeneralSetup.objects.exists()
