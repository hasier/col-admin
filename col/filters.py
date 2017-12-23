from datetime import datetime, timezone

from django.contrib.admin.filters import SimpleListFilter
from django.db.models.expressions import Case, F, Func, Value, When
from django.db.models.query_utils import Q

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
            value = datetime.strptime(value, '%d/%m/%Y')
        else:
            value = datetime.now(timezone.utc)

        date = value.date()
        setup = GeneralSetup.get_for_date(date)

        previous_renewal = setup.get_previous_renewal(date)

        if setup.does_vote_eligibility_need_renewal:
            qs = queryset.filter(
                memberships__effective_from__gte=Case(
                    When(memberships__member_type__tier__needs_renewal=False,
                         then=Func(Value(setup.valid_from), F('memberships__member_type__tier__usable_from'),
                                   function='LEAST')),
                    default=Case(
                        When(~Q(memberships__member_type__tier__usable_until=None)
                             & Q(memberships__member_type__tier__usable_until__gt=previous_renewal)
                             & Q(memberships__member_type__tier__usable_until__lt=value),
                             then=F('memberships__member_type__tier__usable_from')),
                        default=previous_renewal
                    )
                ),
            )
        else:
            qs = queryset.filter(memberships__effective_from__gte=setup.valid_from)

        close_eligible_members_diff = get_timedelta_from_unit(
            setup.time_before_vote_to_close_eligible_members, setup.time_unit_before_vote_to_close_eligible_members
        )
        vote_since_membership_diff = get_timedelta_from_unit(
            setup.time_to_vote_since_membership, setup.time_unit_to_vote_since_membership
        )

        qs = qs.filter(
            memberships__effective_from__lte=Case(
                When(memberships__is_renewal=True,
                     then=date - close_eligible_members_diff),
                default=min(date - close_eligible_members_diff, date - vote_since_membership_diff)
            ),
            memberships__member_type__tier__can_vote=True,
        ).order_by('id', '-memberships__effective_from').distinct('id')
        return qs
