from datetime import datetime, timezone
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.forms.fields import Field

from col import models


class GeneralSetupForm(ModelForm):
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

        if self.instance.pk:
            valid_from = self.instance.valid_from
        else:
            valid_from = self.cleaned_data.get('valid_from')
        valid_until = self.cleaned_data.get('valid_until')
        if valid_until and valid_until < valid_from:
            errors['valid_until'] = 'The end date must happen later than the beginning'
        else:
            last = models.GeneralSetup.get_last()
            if last:
                if last.pk != self.instance.pk:
                    # If there is a previous GeneralSetup and it is not the currently edited instance...
                    if not last.valid_until:
                        # We validate that the previous GeneralSetup needs to be closed first
                        errors['valid_until'] = 'Cannot add a new setup until the previous is closed'
                    else:
                        # Otherwise, the current valid_from is taken from the last day for the last GeneralSetup
                        self.instance.valid_from = last.valid_until
            else:
                # If there is no previous GeneralSetup, the current valid_from is now
                self.instance.valid_from = datetime.now(timezone.utc)

        if errors:
            raise ValidationError(errors)

        return self.cleaned_data
