from __future__ import absolute_import, unicode_literals

from datetime import datetime, timezone

from django.contrib import admin
from django.db.models.fields import TextField

from col import forms, models
from col.filters import EligibleForVoteParticipantFilter
from col.forms import InlineMembershipForm, ParticipantForm
from col.formsets import RequiredOnceInlineFormSet
from col.mixins import AppendOnlyModel, TextAreaToInputMixin, ViewColumnMixin


class HealthInfoInline(admin.TabularInline):
    model = models.HealthInfo
    extra = 1
    can_delete = False


class EmergencyContactInline(TextAreaToInputMixin, admin.TabularInline):
    model = models.EmergencyContact
    formset = RequiredOnceInlineFormSet
    area_to_input_field_names = ['full_name', 'phone', 'relation']
    extra = 1
    can_delete = False

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super(EmergencyContactInline, self).formfield_for_dbfield(db_field, request, **kwargs)
        if isinstance(db_field, TextField):
            formfield.widget.attrs.update(style='width: 90%;')
        return formfield


class MembershipInline(TextAreaToInputMixin, admin.TabularInline):
    model = models.Membership
    form = InlineMembershipForm
    area_to_input_field_names = ['notes']
    extra = 1
    can_delete = False


@admin.register(models.Family)
class FamilyAdmin(TextAreaToInputMixin, admin.ModelAdmin):
    actions = None
    area_to_input_field_names = ['family_name']
    list_display = ['family_name', 'get_family_members']
    readonly_fields = ['get_family_members']

    def get_family_members(self, obj):
        return ','.join((repr(o) for o in obj.family_members.all()))

    get_family_members.short_description = 'Family members'

    def get_ordering(self, request):
        return ['created_at']

    def get_queryset(self, request):
        return super(FamilyAdmin, self).get_queryset(request).prefetch_related('family_members')

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        return []


@admin.register(models.Participant)
class ParticipantAdmin(TextAreaToInputMixin, admin.ModelAdmin):
    actions = None
    form = ParticipantForm
    date_hierarchy = 'created_at'
    area_to_input_field_names = ['name', 'surname', 'postcode', 'phone']
    list_filter = [EligibleForVoteParticipantFilter]
    inlines = [HealthInfoInline, EmergencyContactInline, MembershipInline]

    def get_ordering(self, request):
        return ['created_at']

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.Membership)
class MembershipAdmin(AppendOnlyModel, admin.ModelAdmin):
    date_hierarchy = 'form_filled'
    readonly_fields = ['member_type', 'participant', 'effective_from', 'form_filled', 'paid', 'amount_paid',
                       'payment_method']
    change_view_submit_mode = AppendOnlyModel.JUST_SAVE_MODE

    def get_ordering(self, request):
        return ['created_at']

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.Tier)
class TierAdmin(TextAreaToInputMixin, admin.ModelAdmin):
    area_to_input_field_names = ['name']

    def get_ordering(self, request):
        return ['name']

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        readonly = ()
        if obj:
            restrict_by_date = obj.usable_until and obj.usable_until < datetime.now(timezone.utc).date()
            if restrict_by_date or (obj and any(mc.memberships.count() for mc in obj.membership_combinations.all())):
                readonly += ('name', 'usable_from', 'can_vote', 'needs_renewal')
            if restrict_by_date:
                readonly += ('usable_until',)
        return readonly + self.readonly_fields


@admin.register(models.MemberType)
class MemberTypeAdmin(TextAreaToInputMixin, admin.ModelAdmin):
    area_to_input_field_names = ['type_name']
    list_display = ['type_name', 'notes']

    def get_ordering(self, request):
        return ['type_name']

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj and any(mc.memberships.count() for mc in obj.membership_combinations.all()):
            return ('type_name',) + self.readonly_fields
        return self.readonly_fields


@admin.register(models.MemberTypeTier)
class MemberTypeTierAdmin(TextAreaToInputMixin, admin.ModelAdmin):
    def get_ordering(self, request):
        return ['member_type__type_name', 'tier__name']

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.memberships.count():
            return ('member_type', 'tier', 'base_amount') + self.readonly_fields
        return self.readonly_fields


@admin.register(models.GeneralSetup)
class GeneralSetupAdmin(ViewColumnMixin, AppendOnlyModel, admin.ModelAdmin):
    actions = None
    form = forms.GeneralSetupForm
    change_view_submit_mode = AppendOnlyModel.JUST_SAVE_MODE
    list_display = ['get_view', 'valid_from', 'valid_until', 'days_to_vote_since_membership',
                    'does_vote_eligibility_need_renewal', 'renewal_month', 'renewal_grace_months_period']
    readonly_fields = ['valid_from', 'days_to_vote_since_membership', 'does_vote_eligibility_need_renewal',
                       'renewal_month', 'renewal_grace_months_period']

    def get_ordering(self, request):
        return ['-created_at']

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False

    def get_exclude(self, request, obj=None):
        if obj:
            return []
        return ['valid_from']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            readonly = list(self.readonly_fields)
            if obj.valid_until:
                last = models.GeneralSetup.get_last()
                if last and last.pk != obj.pk:
                    readonly.insert(1, 'valid_until')
            return readonly
        return []
