from datetime import datetime, timezone

from django.contrib.admin.filters import SimpleListFilter
from django.db.models import Case, When, DateField, DurationField
from django.db.models.expressions import F, Value
from django.db.models.functions import Coalesce

from col.models import GeneralSetup
from col.utils import get_timedelta_from_unit


class EligibleForVoteParticipantFilter(SimpleListFilter):
    title = 'Is eligible for vote'
    parameter_name = 'vote_eligible'

    def __init__(self, *args, **kwargs):
        super(EligibleForVoteParticipantFilter, self).__init__(*args, **kwargs)

    def lookups(self, request, model_admin):
        return (
            ('today', 'Today'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset

        if value != 'today':
            value = datetime.strptime(value, '%Y/%m/%d')
        else:
            value = datetime.now(timezone.utc)

        date = value.date()
        setup = GeneralSetup.get_for_date(date)

        vote_since_membership_diff = get_timedelta_from_unit(
            setup.time_to_vote_since_membership, setup.time_unit_to_vote_since_membership
        )

        return (
            queryset
            .annotate(
                reference_date=Value(date, output_field=DateField()),
                vote_interval=Value(f'{setup.minimum_age_to_vote} YEARS', output_field=DurationField()),
            )
            .filter(
                reference_date__between=(
                    Case(
                        When(
                            memberships__is_renewal=True,
                            then=F('memberships__effective_from'),
                        ),
                        default=F('memberships__effective_from') + vote_since_membership_diff,
                        output_field=DateField(),
                    ),
                    Coalesce('memberships__effective_until', Value(date.max)),
                ),
                reference_date__lte=F('vote_interval') + F('date_of_birth'),
                memberships__member_type__tier__can_vote=True,
            )
        ).order_by('id', '-memberships__effective_from').distinct('id')


class RequiresAttentionFilter(SimpleListFilter):
    title = 'Requires attention and updates'
    parameter_name = 'requires_attention'

    def __init__(self, *args, **kwargs):
        super(RequiresAttentionFilter, self).__init__(*args, **kwargs)

    def lookups(self, request, model_admin):
        return (
            ('1', 'Check participants'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset

        if value != '1':
            return queryset

        return queryset.filter(
            Q(address=None) |
            Q(address='') |
            Q(postcode=None) |
            Q(postcode='') |
            Q(phone=None) |
            Q(phone='') |
            Q(email=None) |
            Q(email='') |
            Q(contact_info=None) |
            Q(emergency_contacts=None) |
            Q(memberships__paid=None)
        )
