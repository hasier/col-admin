from datetime import datetime, timezone

from django import forms
from django.core.exceptions import ValidationError

from apps.membership import models


class GeneralSetupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields['time_to_vote_since_membership'].label = ''
            self.fields['time_unit_to_vote_since_membership'].label = ''

    def clean(self):
        super().clean()
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
                errors[
                    'valid_until'
                ] = f'The new setup must happen later than the last one: {last.valid_from}'

        if errors:
            raise ValidationError(errors)

        return self.cleaned_data


class ParticipantForm(forms.ModelForm):
    def clean(self):
        super().clean()
        errors = dict()
        self.instance.date_of_birth = self.cleaned_data['date_of_birth']
        if self.instance.is_under_aged:
            if self.cleaned_data.get('family'):
                for participant in self.cleaned_data['family'].family_members.all():
                    if not participant.is_under_aged:
                        break
                else:
                    errors['family'] = (
                        'An under aged participant must belong to a family '
                        'with at least one adult participant'
                    )
            else:
                errors['family'] = (
                    'An under aged participant must belong to a family, '
                    'and the family must have at least one adult participant'
                )

        if errors:
            raise ValidationError(errors)

        return self.cleaned_data


class MembershipForm(forms.ModelForm):
    def clean(self):
        super().clean()
        errors = dict()
        if 'tier' in self.cleaned_data and not self.cleaned_data['tier'].is_usable_for(
            self.cleaned_data['effective_from']
        ):
            errors['effective_from'] = 'The selected tier is not available for this period'

        if errors:
            raise ValidationError(errors)

        return self.cleaned_data


class AddMembershipForm(forms.Form):
    participant = forms.ModelChoiceField(queryset=models.Participant.objects.all(), required=True)
