from abc import ABC

from django.contrib.admin import SimpleListFilter


class OnlyInputFilter(ABC, SimpleListFilter):
    block_attrs = {
        'display': 'flex',
        'flex-direction': 'column',
        'justify-content': 'flex-end',
    }
    disable_submit_on_filtered = False

    def __init__(self, *args, **kwargs):
        super(OnlyInputFilter, self).__init__(*args, **kwargs)

    def lookups(self, request, model_admin):
        return ((),)

    def choices(self, changelist):
        # Grab only the "all" option.
        all_choice = next(super().choices(changelist))
        all_choice['query_parts'] = (
            (k, v) for k, v in changelist.get_filters_params().items() if k != self.parameter_name
        )
        all_choice['block_attrs'] = self.block_attrs
        all_choice['disable_submit_on_filtered'] = self.disable_submit_on_filtered

        yield all_choice
