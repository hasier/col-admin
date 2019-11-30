from django.core.exceptions import ValidationError
from django.forms.fields import Field

from common.utils.form import RequiredOnceInlineFormSet


class ContactInfoInlineFormset(RequiredOnceInlineFormSet):
    def clean(self):
        for form in self.forms:
            if not form.is_valid():
                return

            if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                if not self.instance.is_under_aged:
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
