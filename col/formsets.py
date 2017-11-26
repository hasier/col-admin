from django.forms.models import BaseInlineFormSet


class RequiredOnceInlineFormSet(BaseInlineFormSet):
    """
    Generates an inline formset that is required
    """

    def _construct_form(self, i, **kwargs):
        """
        Override the method to change the form attribute empty_permitted
        """
        form = super(RequiredOnceInlineFormSet, self)._construct_form(i, **kwargs)
        if not self.queryset.count():
            form.empty_permitted = False
        return form
