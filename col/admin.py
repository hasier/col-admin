from __future__ import absolute_import, unicode_literals

from copy import deepcopy

from django.contrib import admin
from django.contrib.admin import helpers
from django.db.models.fields import TextField
from django.shortcuts import render

from col import forms, models
from col.constants import TIME_UNIT_CHOICES
from col.filters import EligibleForVoteParticipantFilter
from col.forms import InlineMembershipForm, ParticipantForm
from col.formsets import RequiredOnceInlineFormSet
from col.mixins import AppendOnlyModel, RemoveDeleteActionMixin, TextAreaToInputMixin, ViewColumnMixin


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
    exclude = ['is_renewal']
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


def generate_participant_table(modeladmin, request, queryset):
    queryset = queryset.order_by('surname')
    return render(request, 'col/participant_export.html', context=dict(participants=queryset.all()))


generate_participant_table.short_description = "Generate participant PDF"


@admin.register(models.Participant)
class ParticipantAdmin(RemoveDeleteActionMixin, TextAreaToInputMixin, admin.ModelAdmin):
    actions = [generate_participant_table]
    form = ParticipantForm
    area_to_input_field_names = ['name', 'surname', 'postcode', 'phone']
    list_filter = [EligibleForVoteParticipantFilter]
    inlines = [HealthInfoInline, EmergencyContactInline, MembershipInline]

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        try:
            action_index = int(request.POST.get('index', 0))
        except ValueError:
            action_index = 0

        try:
            action = request.POST.getlist('action')[action_index]
        except IndexError:
            action = None

        # If the action is generate_participant_table and no check box has been marked
        if action == generate_participant_table.__name__ and not request.POST.getlist(helpers.ACTION_CHECKBOX_NAME):
            request.POST._mutable = True
            # Activate to select across pages and avoid PK filter
            request.POST['select_across'] = True
            # Add fake data to simulate marked checks
            request.POST.setlist(helpers.ACTION_CHECKBOX_NAME, [1])
            request.POST._mutable = False

        return super(ParticipantAdmin, self).changelist_view(request, extra_context=extra_context)


@admin.register(models.Membership)
class MembershipAdmin(AppendOnlyModel, admin.ModelAdmin):
    date_hierarchy = 'form_filled'
    readonly_fields = ['member_type', 'participant', 'effective_from', 'form_filled', 'paid', 'amount_paid',
                       'payment_method', 'is_renewal']
    change_view_submit_mode = AppendOnlyModel.JUST_SAVE_MODE

    def get_ordering(self, request):
        return ['created_at']

    def has_add_permission(self, request):
        return False

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
            if any(mc.memberships.count() for mc in obj.membership_combinations.all()):
                readonly += ('name', 'can_vote', 'needs_renewal', 'usable_from')
            if obj.usable_until:
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
    fieldsets = (
        (None, {
            'fields': ['valid_until', 'minimum_age_to_vote', 'does_vote_eligibility_need_renewal',
                       'renewal_month', 'renewal_grace_months_period']
        }),
        ('Time to vote since membershp', {
            'fields': ('time_to_vote_since_membership', 'time_unit_to_vote_since_membership')
        }),
        ('Time before vote to close eligible members', {
            'fields': ('time_before_vote_to_close_eligible_members', 'time_unit_before_vote_to_close_eligible_members')
        })
    )
    list_display = ['get_view', 'valid_from', 'valid_until', 'get_time_to_vote_since_membership',
                    'get_time_before_vote_to_close_eligible_members', 'minimum_age_to_vote',
                    'does_vote_eligibility_need_renewal', 'renewal_month', 'renewal_grace_months_period']
    readonly_fields = ['valid_from', 'time_to_vote_since_membership', 'time_unit_to_vote_since_membership',
                       'time_before_vote_to_close_eligible_members', 'time_unit_before_vote_to_close_eligible_members',
                       'minimum_age_to_vote', 'does_vote_eligibility_need_renewal', 'renewal_month',
                       'renewal_grace_months_period']

    def get_time_to_vote_since_membership(self, obj):
        return '{} {}'.format(
            obj.time_to_vote_since_membership, TIME_UNIT_CHOICES[obj.time_unit_to_vote_since_membership].lower()
        )

    get_time_to_vote_since_membership.short_description = 'Time to vote since membership'

    def get_time_before_vote_to_close_eligible_members(self, obj):
        return '{} {}'.format(obj.time_before_vote_to_close_eligible_members,
                              TIME_UNIT_CHOICES[obj.time_unit_before_vote_to_close_eligible_members].lower())

    get_time_before_vote_to_close_eligible_members.short_description = 'Time before vote to close eligible members'

    def get_ordering(self, request):
        return ['-created_at']

    def has_add_permission(self, request):
        setup = models.GeneralSetup.get_current()
        return request.user.is_superuser and (setup is None or setup.valid_until is not None)

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False

    def get_exclude(self, request, obj=None):
        if obj or not models.GeneralSetup.objects.exists():
            return []
        return ['valid_from']

    def get_fieldsets(self, request, obj=None):
        if obj or not models.GeneralSetup.objects.exists():
            fieldsets = deepcopy(self.fieldsets)
            fieldsets[0][1]['fields'].insert(0, 'valid_from')
            return fieldsets
        return self.fieldsets

    def get_readonly_fields(self, request, obj=None):
        if obj:
            readonly = list(self.readonly_fields)
            if obj.valid_until:
                last = models.GeneralSetup.get_current()
                if last is None or last.pk != obj.pk:
                    readonly.insert(1, 'valid_until')
            return readonly
        return []
