from datetime import datetime, timezone

from django.core.exceptions import ValidationError
from django.forms import ModelForm

from apps.membership import models


class GeneralSetupForm(ModelForm):
    def clean(self):
        super(GeneralSetupForm, self).clean()
        errors = dict()

        if self.instance.pk:
            valid_from = self.instance.valid_from
        else:
            valid_from = self.cleaned_data.get('valid_from')

        if not valid_from:
            self.instance.valid_from = datetime.now(timezone.utc)

        last = models.GeneralSetup.get_last()
        if last:
            if last.pk != self.instance.pk and valid_from < last.valid_from:
                errors['valid_until'] = f'The new setup must happen later than the last one: {last.valid_from}'

        if errors:
            raise ValidationError(errors)

        return self.cleaned_data


class ParticipantForm(ModelForm):
    def clean(self):
        super(ParticipantForm, self).clean()
        errors = dict()
        self.instance.date_of_birth = self.cleaned_data['date_of_birth']
        if not self.instance.is_legal_aged:
            if self.cleaned_data.get('family'):
                for participant in self.cleaned_data['family'].family_members.all():
                    if participant.is_legal_aged:
                        break
                else:
                    errors['family'] = 'An under aged participant must belong to a family ' \
                                       'with at least one adult participant'
            else:
                errors['family'] = 'An under aged participant must belong to a family, ' \
                                   'and the family must have at least one adult participant'

        if errors:
            raise ValidationError(errors)

        return self.cleaned_data


class InlineMembershipForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'instance' in kwargs:
            for field_name in ('member_type', 'participant', 'effective_from', 'form_filled', 'amount_paid',
                               'payment_method'):
                self.fields[field_name].disabled = True
            if kwargs['instance'].paid:
                self.fields['paid'].disabled = True

    def clean(self):
        super(InlineMembershipForm, self).clean()
        errors = dict()
        if not self.cleaned_data['member_type'].is_usable_for(self.cleaned_data['effective_from']):
            errors['effective_from'] = 'The selected tier is not available for this period'

        if errors:
            raise ValidationError(errors)

        return self.cleaned_data