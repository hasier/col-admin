from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from dateutil.rrule import YEARLY, rrule
from django.db import models
from django.utils import timezone
from memoize import delete_memoized, memoize

from apps.membership.constants import PAYMENT_METHODS, TIME_UNIT_CHOICES
from apps.membership.templatetags.membership import is_membership_setup_initialized
from apps.membership.utils import get_timedelta_from_unit
from common.model_utils import Loggable


class GeneralSetup(Loggable, models.Model):
    valid_from = models.DateField(db_index=True)
    time_to_vote_since_membership = models.PositiveIntegerField()
    time_unit_to_vote_since_membership = models.PositiveIntegerField(choices=sorted(TIME_UNIT_CHOICES.items()))
    minimum_age_to_vote = models.PositiveIntegerField()
    renewal_month = models.PositiveIntegerField(null=True, blank=True)

    @classmethod
    @memoize(86400)
    def get_last(cls):
        return cls.objects.order_by('-valid_from').first()

    @classmethod
    @memoize(86400)
    def get_for_date(cls, date):
        return cls.objects.filter(valid_from__lte=date).order_by('-valid_from').first()

    @classmethod
    @memoize(3600)
    def get_current(cls):
        return cls.get_for_date(timezone.now())

    @classmethod
    @memoize(3600)
    def get_next(cls, date_from):
        return cls.objects.filter(valid_from__gt=date_from).order_by('valid_from').first()

    def get_previous_renewal(self, from_date):
        dtstart = datetime(from_date.year - 1, from_date.month, 1) + relativedelta(months=1)
        return max(self.valid_from, rrule(YEARLY, dtstart=dtstart, bymonth=self.renewal_month, count=1)[0].date())

    def get_next_renewal(self, from_date):
        dtstart = datetime(from_date.year, from_date.month, 1)
        next_setup = self.get_next(self.valid_from)
        return min(
            next_setup.valid_from if next_setup else date.max,
            rrule(YEARLY, dtstart=dtstart, bymonth=self.renewal_month, count=1)[0].date()
        )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        delete_memoized(self.__class__.get_last)
        delete_memoized(self.__class__.get_for_date)
        delete_memoized(self.__class__.get_current)
        delete_memoized(self.__class__.get_next)
        delete_memoized(is_membership_setup_initialized)
        return super(GeneralSetup, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                              update_fields=update_fields)


class Family(Loggable, models.Model):
    class Meta:
        verbose_name_plural = 'families'

    family_name = models.TextField()

    def __str__(self):
        return self.family_name


class Participant(Loggable, models.Model):
    name = models.TextField()
    surname = models.TextField()
    date_of_birth = models.DateField()
    family = models.ForeignKey(Family, null=True, blank=True, on_delete=models.PROTECT, related_name='family_members')
    participation_form_filled = models.DateField()

    @property
    def age(self):
        return relativedelta(timezone.now().date(), self.date_of_birth).years

    @property
    def is_legal_aged(self):
        return self.age >= 18

    def __str__(self):
        return '{} {}'.format(self.name, self.surname)


class ContactInfo(Loggable, models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name='contact_info')
    address = models.TextField(blank=True)
    postcode = models.TextField(blank=True)
    phone = models.TextField(blank=True)
    email = models.EmailField(blank=True)


class HealthInfo(Loggable, models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name='health_info')
    height = models.PositiveIntegerField(null=True, blank=True)
    weight = models.PositiveIntegerField(null=True, blank=True)
    info = models.TextField()


class EmergencyContact(Loggable, models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name='emergency_contacts')
    full_name = models.TextField()
    phone = models.TextField()
    relation = models.TextField()

    def __str__(self):
        return self.full_name


class MemberType(Loggable, models.Model):
    type_name = models.TextField()
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.type_name


class Tier(Loggable, models.Model):
    name = models.TextField()
    usable_from = models.DateField()
    usable_until = models.DateField(null=True, blank=True)
    member_type = models.ForeignKey(MemberType, on_delete=models.PROTECT, related_name='tiers')
    can_vote = models.BooleanField()
    needs_renewal = models.BooleanField()
    base_amount = models.PositiveIntegerField()

    def is_usable_for(self, ref_date):
        return self.usable_from <= ref_date and (self.usable_until is None or self.usable_until >= ref_date)

    def __str__(self):
        return '{} ({} - {})'.format(self.name, self.usable_from, self.usable_until or '')


class Membership(Loggable, models.Model):
    tier = models.ForeignKey(Tier, on_delete=models.PROTECT, related_name='memberships')
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name='memberships')
    effective_from = models.DateField()
    effective_until = models.DateField(null=True, blank=True)
    form_filled = models.DateField()
    paid = models.DateField(null=True, blank=True)
    amount_paid = models.PositiveIntegerField()
    payment_method = models.PositiveIntegerField(choices=sorted(PAYMENT_METHODS.items()))
    is_renewal = models.BooleanField()
    notes = models.TextField(null=True, blank=True)

    def is_active_on(self, on_date):
        if isinstance(on_date, datetime):
            on_date = on_date.date()

        return self.effective_from <= on_date < (self.effective_until or date.max)

    @property
    def is_active(self):
        return self.is_active_on(timezone.now())

    def __str__(self):
        return '{} membership for {}'.format(self.effective_from, self.participant)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        try:
            last_membership = (
                self.__class__.objects
                .filter(participant_id=self.participant_id)
                .order_by('-effective_from')
            )[0]
        except IndexError:
            self.is_renewal = False
        else:
            # A new membership can only vote after time_to_vote_since_membership
            setup = GeneralSetup.get_for_date(self.effective_from)
            delta = get_timedelta_from_unit(
                setup.time_to_vote_since_membership, setup.time_unit_to_vote_since_membership
            )
            # If the renewing member has stopped being member for longer than that, it is not a renewal
            self.is_renewal = last_membership.is_active_on(self.effective_from - delta)

        if self.effective_from and not self.effective_until:
            self.effective_until = GeneralSetup.get_for_date(self.effective_from).get_next_renewal(self.effective_from)

        super(Membership, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
