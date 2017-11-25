from __future__ import absolute_import, unicode_literals

from django.contrib import admin
from django.db.models.fields import TextField
from django.forms.widgets import TextInput

from col import forms, models
from col.mixins import ViewColumnMixin


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

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super(EmergencyContactInline, self).formfield_for_dbfield(db_field, request, **kwargs)
        if isinstance(db_field, TextField):
            formfield.widget.attrs.update(style='width: 90%;')
        return formfield


class MembershipInline(admin.TabularInline):
    model = models.Membership
    extra = 1
    can_delete = False


@admin.register(models.Family)
class FamilyAdmin(admin.ModelAdmin):
    def get_ordering(self, request):
        return ['created_at']

    def get_model_perms(self, request):
        return {}

    def has_delete_permission(self, request, obj=None):
        return False


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
class GeneralSetupAdmin(ViewColumnMixin, admin.ModelAdmin):
    actions = None
    form = forms.GeneralSetupForm
    exclude = ['valid_from']

    def get_ordering(self, request):
        return ['-created_at']

    def get_list_display(self, request):
        return ['get_view', 'valid_from'] + self.get_fields(request)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['days_to_vote_since_membership', 'days_to_be_staff_since_membership',
                    'vote_allowed_permanently', 'renewal_month', 'renewal_grace_months_period']
        return []
