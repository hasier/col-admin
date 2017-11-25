from django.contrib.admin.utils import unquote
from django.utils.encoding import force_text

from col.utils import ExtraContextOriginalDict


class ViewColumnMixin(object):
    def get_view(self, obj):
        return 'View'
    get_view.short_description = ''
    get_view.admin_order_field = None


class AppendOnlyModel(object):
    """
    Disables the edition from a ModelAdmin, hiding the Save buttons and making all fields readonly.

    `readonly_fields` should only specify the additional readonly columns apart from the model fields.
    `editable_fields` allows to specify which are the ones that should be available in the add page.
    """

    editable_fields = []

    def get_editable_fields(self, request, obj=None):
        return self.editable_fields

    def get_readonly_fields(self, request, obj=None):
        return super(AppendOnlyModel, self).get_readonly_fields(request, obj=obj)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if object_id is not None:
            extra_context = extra_context or dict()
            if 'original' not in extra_context:
                extra_context['original'] = dict()
            # Add tweaks to the title and to hide all save buttons
            extra_context['original']['hide_submit_line'] = True
            extra_context['original'] = ExtraContextOriginalDict(self.get_object(request, unquote(object_id)),
                                                                 **extra_context['original'])
            extra_context['title'] = force_text(self.model._meta.verbose_name)
        return super(AppendOnlyModel, self).change_view(request, object_id,
                                                        form_url=form_url, extra_context=extra_context)

    def changelist_view(self, request, extra_context=None):
        if not extra_context or 'title' not in extra_context:
            extra_context = extra_context or dict()
            extra_context['title'] = force_text(self.model._meta.verbose_name_plural)
        return super(AppendOnlyModel, self).changelist_view(request, extra_context=extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or dict()
        if 'original' not in extra_context:
            extra_context['original'] = dict()
        # Add tweaks to just display the save button
        extra_context['original']['just_save'] = True
        extra_context['original'] = ExtraContextOriginalDict(None, **extra_context['original'])
        return super(AppendOnlyModel, self).add_view(request, form_url=form_url, extra_context=extra_context)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            # obj is None, so this is an edit, disable all fields
            return self.readonly_fields + self.get_editable_fields(request, obj=obj)
        # This is an addition, no readonly to show
        return []
