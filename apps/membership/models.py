from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from dateutil.rrule import YEARLY, rrule
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.dates import MONTHS
from memoize import memoize

from apps.membership.constants import PaymentMethod, TimeUnit
from common.model_utils import Loggable


class GeneralSetup(Loggable, models.Model):
    valid_from = models.DateField(db_index=True)
    time_to_vote_since_membership = models.PositiveIntegerField()
    time_unit_to_vote_since_membership = models.TextField(choices=TimeUnit.choices())
    minimum_age_to_vote = models.PositiveIntegerField()
    renewal_month = models.PositiveIntegerField(
        null=True, blank=True, choices=sorted(MONTHS.items())
    )

    @classmethod
    @memoize(86400)
    def get_last(cls):
        return cls.objects.order_by('-valid_from').first()

    @classmethod
    @memoize(86400)
    def get_for_date(cls, ref_date):
        return cls.objects.filter(valid_from__lte=ref_date).order_by('-valid_from').first()

    @classmethod
    @memoize(3600)
    def get_current(cls):
        return cls.get_for_date(timezone.now())

    @classmethod
    @memoize(3600)
    def get_next(cls, date_from):
        return cls.objects.filter(valid_from__gt=date_from).order_by('valid_from').first()

    @classmethod
    @memoize(3600)
    def get_previous(cls, date_from):
        return cls.objects.filter(valid_from__lt=date_from).order_by('-valid_from').first()

    def get_previous_renewal(self, from_date, min_date=None):
        if min_date and self.valid_from > min_date:
            return None

        dtstart = datetime(from_date.year - 1, from_date.month, 1)

        previous_renewal = rrule(YEARLY, dtstart=dtstart, bymonth=self.renewal_month, count=2)[
            0
        ].date()

        previous_setup = self.get_previous(self.valid_from)
        previous_min_date = None
        if previous_setup:
            previous_min_date = previous_setup.get_previous_renewal(
                self.valid_from, min_date=previous_renewal
            )

        return max(previous_min_date or date(1900, 1, 1), previous_renewal)

    def get_next_renewal(self, from_date, max_date=None):
        if max_date and self.valid_from > max_date:
            return None

        dtstart = datetime(from_date.year, from_date.month, 1)

        if dtstart.month == self.renewal_month:
            index = 1
        else:
            index = 0

        next_renewal = rrule(YEARLY, dtstart=dtstart, bymonth=self.renewal_month, count=2)[
            index
        ].date()

        next_setup = self.get_next(self.valid_from)
        next_max_date = None
        if next_setup:
            next_max_date = next_setup.get_next_renewal(
                next_setup.valid_from, max_date=next_renewal
            )

        return min(next_max_date or date.max, next_renewal)


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
    family = models.ForeignKey(
        Family, null=True, blank=True, on_delete=models.PROTECT, related_name='family_members'
    )
    participation_form_filled_on = models.DateField()

    @property
    def age(self):
        return relativedelta(timezone.now().date(), self.date_of_birth).years

    @property
    def is_under_aged(self):
        return self.age < 18

    @property
    def full_name(self):
        return f'{self.name} {self.surname}'

    def __str__(self):
        return self.full_name


class ContactInfo(Loggable, models.Model):
    participant = models.ForeignKey(
        Participant, on_delete=models.PROTECT, related_name='contact_info'
    )
    address = models.TextField(blank=True)
    postcode = models.TextField(blank=True)
    phone = models.TextField(blank=True)
    email = models.EmailField(blank=True)


class HealthInfo(Loggable, models.Model):
    participant = models.ForeignKey(
        Participant, on_delete=models.PROTECT, related_name='health_info'
    )
    height = models.PositiveIntegerField()
    weight = models.PositiveIntegerField(null=True, blank=True)
    info = models.TextField(null=True, blank=True)


class EmergencyContact(Loggable, models.Model):
    participant = models.ForeignKey(
        Participant, on_delete=models.PROTECT, related_name='emergency_contacts'
    )
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
        if isinstance(ref_date, datetime):
            ref_date = ref_date.date()
        return self.usable_from <= ref_date < (self.usable_until or date.max)

    def __str__(self):
        return '{} ({} - {})'.format(self.name, self.usable_from, self.usable_until or 'forever')


class Membership(Loggable, models.Model):
    participant = models.ForeignKey(
        Participant, on_delete=models.PROTECT, related_name='memberships'
    )
    tier = models.ForeignKey(Tier, on_delete=models.PROTECT, related_name='memberships')
    effective_from = models.DateField()
    effective_until = models.DateField(null=True, blank=True)
    form_filled = models.DateField()
    paid_on = models.DateField(null=True, blank=True)
    group_first_membership = models.ForeignKey(
        'Membership', null=True, on_delete=models.PROTECT, related_name='grouped_memberships'
    )
    notes = models.TextField(null=True, blank=True)

    @property
    def amount_paid(self):
        return sum(payment.amount_paid for payment in self.payments.all())

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
        if self.effective_from and not self.effective_until:
            try:
                last_membership = (
                    type(self)
                    .objects.filter(participant_id=self.participant_id)
                    .order_by('-effective_from')
                )[0]
            except IndexError:
                pass
            else:
                if last_membership.is_active_on(self.effective_from):
                    raise ValidationError(
                        dict(
                            effective_from=[
                                'Cannot create a new membership until the previous one '
                                f'({last_membership}) has been closed'
                            ]
                        )
                    )

                # If the renewal stopped being member for longer than a month, it is not a renewal
                effective_from = self.effective_from - relativedelta(months=1)
                if (
                    last_membership.is_active_on(effective_from)
                    and last_membership.tier.can_vote == self.tier.can_vote
                ):
                    self.group_first_membership = (
                        last_membership.group_first_membership or last_membership
                    )

            if self.tier.needs_renewal:
                self.effective_until = GeneralSetup.get_for_date(
                    self.effective_from
                ).get_next_renewal(self.effective_from) - relativedelta(days=1)

        super(Membership, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )


class MembershipPayment(models.Model):
    membership = models.ForeignKey(Membership, on_delete=models.PROTECT, related_name='payments')
    amount_paid = models.PositiveIntegerField()
    payment_method = models.TextField(choices=PaymentMethod.choices())


class MembershipPeriod(models.Model):
    id = models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    participant = models.ForeignKey(
        Participant, on_delete=models.DO_NOTHING, related_name='membership_periods'
    )
    can_vote = models.BooleanField()
    effective_from = models.DateField()
    effective_until = models.DateField()

    class Meta:
        managed = False
        db_table = 'membership_membershipperiod'
