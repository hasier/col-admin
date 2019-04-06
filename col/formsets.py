from django.core.exceptions import ValidationError
from django.forms.fields import Field
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


class ContactInfoInlineFormset(RequiredOnceInlineFormSet):
    def clean(self):
        for form in self.forms:
            if not form.is_valid():
                return

            if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                if self.instance.is_legal_aged:
                    errors = dict()
                    for field_name, value in (
                        ('address', form.cleaned_data.get('address')),
                        ('postcode', form.cleaned_data.get('postcode')),
                        ('phone', form.cleaned_data.get('phone')),
                        ('email', form.cleaned_data.get('email')),
                    ):
                        if value is None:
                            errors[field_name] = Field.default_error_messages['required']

                    if errors:
                        raise ValidationError(errors)
