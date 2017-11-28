from datetime import datetime, timezone

from django.contrib.admin.filters import SimpleListFilter
from django.template.loader import get_template
from django.contrib.admin.templatetags.admin_list import register


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
        value = value.date()

        return queryset
