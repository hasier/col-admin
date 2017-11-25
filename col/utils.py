from django.forms.models import BaseInlineFormSet
from django.utils.encoding import force_text
from django.utils.six import python_2_unicode_compatible


def limited_inline_formset_builder(max_num):
    class LimitedInlineFormSet(BaseInlineFormSet):
        def get_queryset(self):
            return super(LimitedInlineFormSet, self).get_queryset()[:max_num]

    return LimitedInlineFormSet


@python_2_unicode_compatible
class ExtraContextOriginalDict(dict):
    """
    Special dictionary to inject into Django views as extra content with the 'original' key. The value inside the
    'original' key is used by some registered tags, such as `submit_row`.

    Example::

        def change_view(self, request, object_id, form_url='', extra_context=None):
            extra_context = extra_context or dict()
            if 'original' not in extra_context:
                extra_context['original'] = dict()
            extra_context['original']['my_extra_attribute'] = 'some value'
            extra_context['original'] = TemplateOriginalDict(self.get_object(request, unquote(object_id)),
                                                             **extra_context['original'])
            return super(MyParentObject, self).change_view(request, object_id,
                                                           form_url=form_url, extra_context=extra_context)
    """

    def __init__(self, from_obj, seq=None, **kwargs):
        super(ExtraContextOriginalDict, self).__init__(seq=seq, **kwargs)
        self.from_obj = from_obj

    def __str__(self):
        return force_text(self.from_obj)
