from __future__ import absolute_import, unicode_literals

from django.contrib import admin
from django.forms.widgets import TextInput

from col import models


class TextAreaToInputMixin(object):
    area_to_input_field_names = []

    def get_area_to_input_field_names(self):
        return self.area_to_input_field_names

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super(TextAreaToInputMixin, self).formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in self.get_area_to_input_field_names():
            formfield.widget = TextInput(attrs=formfield.widget.attrs)
        return formfield


@admin.register(models.Participant)
class ParticipantAdmin(TextAreaToInputMixin, admin.ModelAdmin):
    area_to_input_field_names = ['name', 'surname', 'postcode', 'phone']

    def get_ordering(self, request):
        return ['created_at']

    def has_delete_permission(self, request, obj=None):
        return False
