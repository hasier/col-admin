from datetime import datetime, timezone
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.forms.fields import Field

from col import models


class GeneralSetupForm(ModelForm):
    # def __init__(self, *args, **kwargs):
    #     super(GeneralSetupForm, self).__init__(*args, **kwargs)
    #     try:
    #         models.GeneralSetup.objects.order_by('-created_at')[0]
    #     except KeyError:
    #         self.fields['valid_from'].required = False

    def clean(self):
        super(GeneralSetupForm, self).clean()
        errors = dict()
        if 'vote_allowed_permanently' in self.cleaned_data and not self.cleaned_data['vote_allowed_permanently']:
            for field_name, value in (
                    ('renewal_month', self.cleaned_data.get('renewal_month')),
                    ('renewal_grace_months_period', self.cleaned_data.get('renewal_grace_months_period'))
            ):
                if value is None:
                    errors[field_name] = Field.default_error_messages['required']

        try:
            last = models.GeneralSetup.objects.order_by('-created_at')[0]
        except IndexError:
            self.instance.valid_from = datetime.now(timezone.utc)
        else:
            if last.pk != self.instance.pk:
                if not last.valid_until:
                    errors['valid_until'] = 'Cannot add a new setup until the previous is closed'
                else:
                    self.instance.valid_from = last.valid_until

        if errors:
            raise ValidationError(errors)

        return self.cleaned_data
