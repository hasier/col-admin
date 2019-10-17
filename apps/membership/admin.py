from django.contrib import admin
from django.contrib.admin import helpers
from django.db.models.fields import TextField
from django.shortcuts import render
from material.admin.options import MaterialModelAdmin
from material.admin.decorators import register

from apps.membership import forms, models
from apps.membership.constants import TIME_UNIT_CHOICES
from apps.membership.filters import EligibleForVoteParticipantFilter, RequiresAttentionFilter
from apps.membership.forms import InlineMembershipForm, ParticipantForm
from apps.membership.formsets import ContactInfoInlineFormset, RequiredOnceInlineFormSet
from common.mixins import AppendOnlyModel, RemoveDeleteActionMixin, TextAreaToInputMixin, ViewColumnMixin


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


class ContactInfoInline(TextAreaToInputMixin, admin.TabularInline):
    model = models.ContactInfo
    formset = ContactInfoInlineFormset
    area_to_input_field_names = ['postcode', 'phone']
    extra = 1
    can_delete = False

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super(ContactInfoInline, self).formfield_for_dbfield(db_field, request, **kwargs)
        if isinstance(db_field, TextField):
            formfield.widget.attrs.update(style='width: 90%;')
        return formfield


class MembershipInline(TextAreaToInputMixin, admin.TabularInline):
    model = models.Membership
    form = InlineMembershipForm
    exclude = ['is_renewal', 'effective_until']
    area_to_input_field_names = ['notes']
    extra = 1
    can_delete = False


@register(models.Family)
class FamilyAdmin(TextAreaToInputMixin, MaterialModelAdmin):
    icon_name = 'child_friendly'

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


@register(models.Participant)
class ParticipantAdmin(RemoveDeleteActionMixin, TextAreaToInputMixin, MaterialModelAdmin):
    icon_name = 'person_outline'

    actions = [generate_participant_table]
    form = ParticipantForm
    area_to_input_field_names = ['name', 'surname']
    list_filter = [EligibleForVoteParticipantFilter, RequiresAttentionFilter]
    inlines = [ContactInfoInline, HealthInfoInline, EmergencyContactInline, MembershipInline]

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


@register(models.Membership)
class MembershipAdmin(AppendOnlyModel, MaterialModelAdmin):
    icon_name = 'card_membership'

    date_hierarchy = 'form_filled'
    readonly_fields = [
        'tier',
        'participant',
        'effective_from',
        'effective_until',
        'form_filled',
        'paid',
        'amount_paid',
        'payment_method',
        'is_renewal',
    ]
    change_view_submit_mode = AppendOnlyModel.JUST_SAVE_MODE

    def get_ordering(self, request):
        return ['created_at']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@register(models.Tier)
class TierAdmin(TextAreaToInputMixin, MaterialModelAdmin):
    icon_name = 'layers'

    area_to_input_field_names = ['name']

    def get_ordering(self, request):
        return ['name']

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        readonly = ()
        if obj:
            if any(mc.memberships.count() for mc in obj.membership_combinations.all()):
                readonly += ('name', 'can_vote', 'needs_renewal', 'usable_from', 'base_amount', 'member_type')
            if obj.usable_until:
                readonly += ('usable_until',)
        return readonly + self.readonly_fields


@register(models.MemberType)
class MemberTypeAdmin(TextAreaToInputMixin, MaterialModelAdmin):
    icon_name = 'people_outline'

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


@register(models.GeneralSetup)
class GeneralSetupAdmin(ViewColumnMixin, AppendOnlyModel, MaterialModelAdmin):
    icon_name = 'settings'

    actions = None
    form = forms.GeneralSetupForm
    change_view_submit_mode = AppendOnlyModel.JUST_SAVE_MODE
    fieldsets = (
        (None, {
            'fields': [
                'minimum_age_to_vote',
                'renewal_month',
            ]
        }),
        ('Time to vote since membership', {
            'fields': ('time_to_vote_since_membership', 'time_unit_to_vote_since_membership')
        }),
    )
    list_display = [
        'get_view',
        'valid_from',
        'get_time_to_vote_since_membership',
        'minimum_age_to_vote',
        'renewal_month',
    ]
    readonly_fields = [
        'valid_from',
        'time_to_vote_since_membership',
        'time_unit_to_vote_since_membership',
        'minimum_age_to_vote',
        'renewal_month',
    ]

    def get_time_to_vote_since_membership(self, obj):
        return '{} {}'.format(
            obj.time_to_vote_since_membership, TIME_UNIT_CHOICES[obj.time_unit_to_vote_since_membership].lower()
        )

    get_time_to_vote_since_membership.short_description = 'Time to vote since membership'

    def get_ordering(self, request):
        return ['-created_at']

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False
