from datetime import datetime

from django.db.models import DateField, Q
from django.db.models.expressions import DurationValue, F, Value
from django.db.models.functions import Coalesce

from apps.membership.models import GeneralSetup
from common.utils.filters import OnlyInputFilter
from contrib.django.postgres.fields import DurationField


class EligibleForVoteParticipantFilter(OnlyInputFilter):
    template = 'admin/date_input_filter.html'

    title = 'Is eligible for vote on'
    parameter_name = 'vote_eligible'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset

        try:
            date = datetime.strptime(value, '%d/%m/%Y').date()
        except ValueError:
            return queryset.none()

        setup = GeneralSetup.get_for_date(date)

        if not setup:
            return queryset.none()

        return (
            (
                queryset.annotate(
                    reference_date=Value(date, output_field=DateField()),
                    min_age=DurationValue(
                        f"{setup.minimum_age_to_vote} YEARS", output_field=DurationField()
                    ),
                    vote_interval=DurationValue(
                        f'{setup.time_to_vote_since_membership} '
                        f'{setup.time_unit_to_vote_since_membership.upper()}',
                        output_field=DurationField(),
                    ),
                ).filter(
                    Q(
                        reference_date__range=(
                            F('membership_periods__effective_from') + F('vote_interval'),
                            Coalesce(
                                'membership_periods__effective_until',
                                Value(date.max, output_field=DateField()),
                                output_field=DateField(),
                            ),
                        )
                    ),
                    Q(
                        reference_date__range=(
                            F('memberships__effective_from'),
                            Coalesce(
                                'memberships__effective_until',
                                Value(date.max, output_field=DateField()),
                                output_field=DateField(),
                            ),
                        )
                    ),
                    memberships__tier__can_vote=True,
                    reference_date__gte=F('min_age') + F('date_of_birth'),
                )
            )
            .order_by('id', '-membership_periods__effective_from')
            .distinct('id')
        )


class RequiresAttentionFilter(OnlyInputFilter):
    template = 'admin/button_filter.html'
    disable_submit_on_filtered = True

    title = 'Requires attention and updates'
    parameter_name = 'requires_attention'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset

        return queryset.filter(
            Q(contact_info=None)
            | Q(contact_info__address=None)
            | Q(contact_info__address='')
            | Q(contact_info__postcode=None)
            | Q(contact_info__postcode='')
            | Q(contact_info__phone=None)
            | Q(contact_info__phone='')
            | Q(contact_info__email=None)
            | Q(contact_info__email='')
            | Q(emergency_contacts=None)
            | Q(memberships__paid_on=None)
        )
