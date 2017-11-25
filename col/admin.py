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


class HealthInfoInline(admin.TabularInline):
    model = models.HealthInfo
    extra = 1
    can_delete = False


class EmergencyContactInline(admin.TabularInline):
    model = models.EmergencyContact
    extra = 1
    can_delete = False


class MembershipInline(admin.TabularInline):
    model = models.Membership
    extra = 1
    can_delete = False


@admin.register(models.Participant)
class ParticipantAdmin(TextAreaToInputMixin, admin.ModelAdmin):
    date_hierarchy = 'created_at'
    area_to_input_field_names = ['name', 'surname', 'postcode', 'phone']
    inlines = [HealthInfoInline, EmergencyContactInline, MembershipInline]

    def get_ordering(self, request):
        return ['created_at']

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.Membership)
class MembershipAdmin(admin.ModelAdmin):
    date_hierarchy = 'form_filled'

    def get_ordering(self, request):
        return ['created_at']

    def get_readonly_fields(self, request, obj=None):
        return self.get_fields(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(models.Tier)
class TierAdmin(TextAreaToInputMixin, admin.ModelAdmin):
    area_to_input_field_names = ['name']

    def get_ordering(self, request):
        return ['-created_at']

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.GeneralSetup)
class GeneralSetupAdmin(admin.ModelAdmin):
    actions = None

    def get_ordering(self, request):
        return ['-created_at']

    def get_list_display(self, request):
        return ['id'] + self.get_fields(request)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False
