from datetime import datetime, timedelta, timezone

from django.contrib.admin.filters import SimpleListFilter
from django.contrib.admin.templatetags.admin_list import register
from django.db.models.expressions import Case, Value, When
from django.template.loader import get_template

from col.models import GeneralSetup


@register.simple_tag
def admin_list_filter(cl, spec):
    choices = list(spec.choices(cl))
    if not len(choices):
        return ''

    tpl = get_template(spec.template)
    return tpl.render({
        'title': spec.title,
        'choices': choices,
        'spec': spec,
    })


class EligibleForVoteParticipantFilter(SimpleListFilter):
    title = 'Is eligible for vote'
    parameter_name = 'vote_eligible'

    def __init__(self, *args, **kwargs):
        super(EligibleForVoteParticipantFilter, self).__init__(*args, **kwargs)

    def lookups(self, request, model_admin):
        return (None,)

    def choices(self, changelist):
        return {}

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            value = datetime.strptime(value, '%d/%m/%Y')
        else:
            value = datetime.now(timezone.utc)

        date = value.date()
        setup = GeneralSetup.get_current()
        effective_from = date - timedelta(days=max(setup.days_to_vote_since_membership,
                                                   setup.days_before_vote_to_close_eligible_members))

        if setup.does_vote_eligibility_need_renewal:
            previous_renewal = max(setup.get_previous_renewal(date), setup.valid_from)
            qs = queryset.filter(
                memberships__effective_from__gt=Case(
                    When(memberships__member_type__tier__needs_renewal=False,
                         then=Value(setup.valid_from)),
                    default=previous_renewal
                ),
            )
        else:
            qs = queryset.filter(memberships__effective_from__gt=setup.valid_from)

        qs = qs.filter(
            memberships__effective_from__lt=date - Case(
                When(memberships__is_renewal=True, then=Value(0)),
                default=effective_from
            ),
            memberships__member_type__tier__can_vote=True,
        )
        return qs
