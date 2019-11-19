import sys
from urllib.parse import urlencode

from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.options import get_content_type_for_model
from django.db.models.fields import TextField
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, path
from material.admin.options import MaterialModelAdmin
from material.admin.decorators import register

from apps.membership import forms, models
from apps.membership.constants import TimeUnit
from apps.membership.filters import EligibleForVoteParticipantFilter, RequiresAttentionFilter
from apps.membership.forms import MembershipForm, ParticipantForm, AddMembershipForm
from apps.membership.formsets import ContactInfoInlineFormset
from apps.membership.templatetags import membership
from common.form_utils import RequiredOnceInlineFormSet
from common.admin_utils import (
    AppendOnlyModelAdminMixin,
    RemoveDeleteActionMixin,
    TextAreaToInputMixin,
    ViewColumnMixin,
)
from contrib.material.admin.options import MaterialTabularInline


class RequiresInitModelAdmin(admin.ModelAdmin):
    def _has_init_permission(self):
        command = sys.argv[1] if len(sys.argv) > 1 else None
        if (
            command not in ('makemigrations', 'migrate', None)
            and not membership.is_membership_setup_initialized()
        ):
            return False
        return True

    def has_view_permission(self, request, obj=None):
        return self._has_init_permission() and super().has_view_permission(request, obj=obj)

    def has_module_permission(self, request):
        return self._has_init_permission() and super().has_module_permission(request)

    def has_add_permission(self, request):
        return self._has_init_permission() and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return self._has_init_permission() and super().has_change_permission(request, obj=obj)

    def has_delete_permission(self, request, obj=None):
        return self._has_init_permission() and super().has_delete_permission(request, obj=obj)


class HealthInfoInline(MaterialTabularInline):
    model = models.HealthInfo
    extra = 1
    can_delete = False


class EmergencyContactInline(TextAreaToInputMixin, MaterialTabularInline):
    model = models.EmergencyContact
    formset = RequiredOnceInlineFormSet
    area_to_input_field_names = ['full_name', 'phone', 'relation']
    extra = 1
    can_delete = False

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if isinstance(db_field, TextField):
            formfield.widget.attrs.update(style='width: 90%;')
        return formfield


class ContactInfoInline(TextAreaToInputMixin, MaterialTabularInline):
    model = models.ContactInfo
    formset = ContactInfoInlineFormset
    area_to_input_field_names = ['postcode', 'phone']
    extra = 1
    can_delete = False

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if isinstance(db_field, TextField):
            formfield.widget.attrs.update(style='width: 90%;')
        return formfield


@register(models.Family)
class FamilyAdmin(RequiresInitModelAdmin, TextAreaToInputMixin, MaterialModelAdmin):
    icon_name = 'child_friendly'

    actions = None
    area_to_input_field_names = ['family_name']
    list_display = ['family_name', 'get_family_members']
    readonly_fields = ['get_family_members']

    def get_family_members(self, obj):
        return ', '.join((repr(o) for o in obj.family_members.all()))

    get_family_members.short_description = 'Family members'

    def get_ordering(self, request):
        return ['created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('family_members')

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields
        return []


def generate_participant_table(modeladmin, request, queryset):
    queryset = queryset.order_by('surname')
    return render(
        request, 'col/participant_export.html', context=dict(participants=queryset.all())
    )


generate_participant_table.short_description = "Generate participant PDF"


@register(models.Participant)
class ParticipantAdmin(
    RequiresInitModelAdmin, RemoveDeleteActionMixin, TextAreaToInputMixin, MaterialModelAdmin
):
    icon_name = 'person_outline'

    actions = [generate_participant_table]
    form = ParticipantForm
    list_display = [
        'full_name',
        'date_of_birth',
        'family',
        'participation_form_filled_on',
    ]
    area_to_input_field_names = ['name', 'surname']
    list_filter = [EligibleForVoteParticipantFilter, RequiresAttentionFilter]
    inlines = [ContactInfoInline, EmergencyContactInline, HealthInfoInline]

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
        if action == generate_participant_table.__name__ and not request.POST.getlist(
            helpers.ACTION_CHECKBOX_NAME
        ):
            request.POST._mutable = True
            # Activate to select across pages and avoid PK filter
            request.POST['select_across'] = True
            # Add fake data to simulate marked checks
            request.POST.setlist(helpers.ACTION_CHECKBOX_NAME, [1])
            request.POST._mutable = False

        return super().changelist_view(request, extra_context=extra_context)


class MembershipPaymentInline(MaterialTabularInline):
    model = models.MembershipPayment
    formset = RequiredOnceInlineFormSet
    extra = 1
    can_delete = False


@register(models.Membership)
class MembershipAdmin(RequiresInitModelAdmin, AppendOnlyModelAdminMixin, MaterialModelAdmin):
    icon_name = 'card_membership'

    form = MembershipForm
    readonly_fields = [
        'tier',
        'participant',
        'effective_from',
        'effective_until',
        'amount_paid',
    ]
    exclude = ['renewed_membership']
    list_display = [
        'participant',
        'tier',
        'effective_from',
        'effective_until',
    ]
    inlines = [MembershipPaymentInline]
    area_to_input_field_names = ['notes']
    change_view_submit_mode = AppendOnlyModelAdminMixin.JUST_SAVE_MODE

    def get_ordering(self, request):
        return ['-created_at']

    def get_exclude(self, request, obj=None):
        exclude = []
        if not obj:
            exclude.append('effective_until')
        return super().get_exclude(request, obj=obj) + exclude

    def get_readonly_fields(self, request, obj=None):
        readonly = []
        if obj:
            for field in ('form_filled', 'paid_on'):
                if getattr(obj, field):
                    readonly.append(field)
        return super().get_readonly_fields(request, obj=obj) + readonly

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        return [
            path(
                'select_participant/',
                self.admin_site.admin_view(self.select_participant),
                name='select_participant',
            )
        ] + super().get_urls()

    def get_form(self, request, obj=None, change=False, **kwargs):
        form_cls = super().get_form(request, obj=obj, change=change, **kwargs)
        if not obj:
            participant_id = request.GET.get('participant_id')
            form_cls.base_fields['participant'].queryset = form_cls.base_fields[
                'participant'
            ].queryset.filter(pk=participant_id)
            form_cls.base_fields['participant'].empty_label = None
            form_cls.base_fields['participant'].initial = form_cls.base_fields[
                'participant'
            ].queryset.get()

        return form_cls

    def add_view(self, request, form_url='', extra_context=None):
        participant_id = request.GET.get('participant_id')
        if participant_id:
            try:
                models.Participant.objects.get(pk=participant_id)
            except models.Participant.DoesNotExist:
                pass
            else:
                return super().add_view(request, form_url=form_url, extra_context=extra_context)

        return HttpResponseRedirect(reverse('admin:select_participant'))

    def select_participant(self, request):
        if request.method == 'POST':
            form = AddMembershipForm(request.POST)
            if form.is_valid():
                params = dict(participant_id=form.cleaned_data['participant'].pk)
                return HttpResponseRedirect(
                    f"{reverse('admin:membership_membership_add')}?{urlencode(params)}"
                )

        else:
            form = AddMembershipForm()

        opts = self.model._meta
        app_label = opts.app_label
        context = {
            **self.admin_site.each_context(request),
            'is_popup': False,
            'preserved_filters': self.get_preserved_filters(request),
            'add': True,
            'change': False,
            'has_view_permission': False,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': False,
            'has_delete_permission': False,
            'has_absolute_url': False,
            'opts': opts,
            'content_type_id': get_content_type_for_model(self.model).pk,
            'save_as': self.save_as,
            'save_on_top': self.save_on_top,
            'app_label': app_label,
            'media': self.media,
            'form': form,
        }

        return render(request, 'col/select_add_membership_participant.html', context)


@register(models.Tier)
class TierAdmin(RequiresInitModelAdmin, TextAreaToInputMixin, MaterialModelAdmin):
    icon_name = 'layers'

    list_display = [
        'get_name',
        'usable_from',
        'usable_until',
        'can_vote',
        'needs_renewal',
    ]
    area_to_input_field_names = ['name']

    def get_name(self, obj):
        return f'{obj.name} ({obj.member_type.type_name})'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('member_type')

    def get_ordering(self, request):
        return ['name']

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        readonly = ()
        if obj:
            if models.Membership.objects.filter(tier=obj).exists():
                readonly += (
                    'name',
                    'can_vote',
                    'needs_renewal',
                    'usable_from',
                    'base_amount',
                    'member_type',
                )
            if obj.usable_until:
                readonly += ('usable_until',)
        return readonly + self.readonly_fields


@register(models.MemberType)
class MemberTypeAdmin(RequiresInitModelAdmin, TextAreaToInputMixin, MaterialModelAdmin):
    icon_name = 'people_outline'

    area_to_input_field_names = ['type_name']
    list_display = ['type_name', 'notes']

    def get_ordering(self, request):
        return ['type_name']

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj and models.Membership.objects.filter(tier__member_type=obj).exists():
            return ('type_name',) + self.readonly_fields
        return self.readonly_fields


@register(models.GeneralSetup)
class GeneralSetupAdmin(ViewColumnMixin, AppendOnlyModelAdminMixin, MaterialModelAdmin):
    icon_name = 'settings'

    actions = None
    form = forms.GeneralSetupForm
    fieldsets = (
        (None, {'fields': ('minimum_age_to_vote', 'renewal_month')}),
        (
            'Time to vote since membership started',
            {'fields': (('time_to_vote_since_membership', 'time_unit_to_vote_since_membership'),)},
        ),
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
            obj.time_to_vote_since_membership,
            TimeUnit.get_from_value(obj.time_unit_to_vote_since_membership).value.lower(),
        )

    get_time_to_vote_since_membership.short_description = 'Time to vote since membership'

    def get_ordering(self, request):
        return ['-created_at']

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False
