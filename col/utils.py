from django.forms.models import BaseInlineFormSet


def limited_inline_formset_builder(max_num):
    class LimitedInlineFormSet(BaseInlineFormSet):
        def get_queryset(self):
            return super(LimitedInlineFormSet, self).get_queryset()[:max_num]

    return LimitedInlineFormSet
