from django.forms import BaseInlineFormSet


def limited_inline_formset_builder(max_num):
    class LimitedInlineFormSet(BaseInlineFormSet):
        def get_queryset(self):
            return super().get_queryset()[:max_num]

    return LimitedInlineFormSet


class RequiredOnceInlineFormSet(BaseInlineFormSet):
    """
    Generates an inline formset that is required
    """

    def _construct_form(self, i, **kwargs):
        """
        Override the method to change the form attribute empty_permitted
        """
        form = super()._construct_form(i, **kwargs)
        if not self.queryset.count():
            form.empty_permitted = False
        return form
