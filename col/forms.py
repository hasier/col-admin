from datetime import datetime, timezone

from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.forms.fields import Field

from col import models


class GeneralSetupForm(ModelForm):
    def clean(self):
        super(GeneralSetupForm, self).clean()
        errors = dict()
        if 'does_vote_eligibility_need_renewal' in self.cleaned_data \
                and not self.cleaned_data['does_vote_eligibility_need_renewal']:
            for field_name, value in (
                    ('renewal_month', self.cleaned_data.get('renewal_month')),
                    ('renewal_grace_months_period', self.cleaned_data.get('renewal_grace_months_period')),
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


class ParticipantForm(ModelForm):
    def clean(self):
        super(ParticipantForm, self).clean()
        errors = dict()
        self.instance.date_of_birth = self.cleaned_data['date_of_birth']
        if self.instance.is_under_aged:
            if self.cleaned_data.get('family'):
                for participant in self.cleaned_data['family'].family_members.all():
                    if not participant.is_under_aged:
                        break
                else:
                    errors['family'] = 'An under aged participant must belong to a family ' \
                                       'with at least one adult participant'
            else:
                errors['family'] = 'An under aged participant must belong to a family, ' \
                                   'and the family must have at least one adult participant'
        else:
            for field_name, value in (
                    ('address', self.cleaned_data.get('address')),
                    ('postcode', self.cleaned_data.get('postcode')),
                    ('phone', self.cleaned_data.get('phone')),
                    ('email', self.cleaned_data.get('email')),
            ):
                if value is None:
                    errors[field_name] = Field.default_error_messages['required']

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
