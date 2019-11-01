from django.forms.widgets import TextInput
from django.utils.encoding import force_text


class ViewColumnMixin(object):
    def get_view(self, obj):
        return 'View'

    get_view.short_description = ''
    get_view.admin_order_field = None


class TextAreaToInputMixin(object):
    area_to_input_field_names = []

    def get_area_to_input_field_names(self):
        return self.area_to_input_field_names

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super(TextAreaToInputMixin, self).formfield_for_dbfield(
            db_field, request, **kwargs
        )
        if db_field.name in self.get_area_to_input_field_names():
            formfield.widget = TextInput(attrs=formfield.widget.attrs)
        return formfield


class AppendOnlyModelAdminMixin(object):
    """
    Disables the edition from a ModelAdmin, hiding the Save buttons and making all fields readonly.

    `readonly_fields` should only specify the additional readonly columns apart from the model fields.
    `editable_fields` allows to specify which are the ones that should be available in the add page.
    """

    JUST_SAVE_MODE = 'just_save'
    HIDE_SUBMIT_LINE_MODE = 'hide_submit_line'

    editable_fields = []
    add_view_submit_mode = JUST_SAVE_MODE
    change_view_submit_mode = HIDE_SUBMIT_LINE_MODE

    def get_editable_fields(self, request, obj=None):
        return self.editable_fields

    def _get_extra_for_mode(self, mode):
        extra = dict()
        if mode == self.JUST_SAVE_MODE:
            extra['show_save_and_add_another'] = False
            extra['show_save_and_continue'] = False
            extra['show_delete_link'] = False

        elif mode == self.HIDE_SUBMIT_LINE_MODE:
            extra['save_on_top'] = False
            extra['submit_buttons_bottom'] = False

        return extra

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if object_id is not None:
            extra_context = extra_context or dict()
            # Add tweaks to the title and to hide all save buttons
            extra_context.update(self._get_extra_for_mode(self.change_view_submit_mode))
            extra_context['title'] = force_text(self.model._meta.verbose_name)
        return super(AppendOnlyModelAdminMixin, self).change_view(
            request, object_id, form_url=form_url, extra_context=extra_context
        )

    def changelist_view(self, request, extra_context=None):
        if not extra_context or 'title' not in extra_context:
            extra_context = extra_context or dict()
            extra_context['title'] = force_text(self.model._meta.verbose_name_plural)
        return super(AppendOnlyModelAdminMixin, self).changelist_view(
            request, extra_context=extra_context
        )

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or dict()
        # Add tweaks to just display the save button
        extra_context.update(self._get_extra_for_mode(self.add_view_submit_mode))
        return super(AppendOnlyModelAdminMixin, self).add_view(
            request, form_url=form_url, extra_context=extra_context
        )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            # obj is None, so this is an edit, disable all fields
            return self.readonly_fields + self.get_editable_fields(request, obj=obj)
        # This is an addition, no readonly to show
        return []


class RemoveDeleteActionMixin(object):
    def get_actions(self, request):
        actions = super(RemoveDeleteActionMixin, self).get_actions(request)
        try:
            del actions['delete_selected']
        except KeyError:
            pass
        return actions
