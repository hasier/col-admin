from datetime import date, datetime, timedelta, timezone

from dateutil.relativedelta import relativedelta
from dateutil.rrule import YEARLY, rrule
from django.db import models
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from memoize import delete_memoized, memoize

from col.constants import PAYMENT_METHODS, TIME_UNIT_CHOICES
from col.templatetags.utils import is_system_initialized


class Loggable(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class GeneralSetup(Loggable, models.Model):
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    time_to_vote_since_membership = models.PositiveIntegerField()
    time_unit_to_vote_since_membership = models.PositiveIntegerField(choices=TIME_UNIT_CHOICES.items())
    time_before_vote_to_close_eligible_members = models.PositiveIntegerField()
    time_unit_before_vote_to_close_eligible_members = models.PositiveIntegerField(choices=TIME_UNIT_CHOICES.items())
    minimum_age_to_vote = models.PositiveIntegerField()
    does_vote_eligibility_need_renewal = models.BooleanField()
    renewal_month = models.PositiveIntegerField(null=True, blank=True)
    renewal_grace_months_period = models.PositiveIntegerField(null=True, blank=True)

    @classmethod
    @memoize(86400)
    def get_last(cls):
        try:
            return cls.objects.order_by(F('valid_until').desc(nulls_first=True))[0]
        except IndexError:
            return None

    @classmethod
    @memoize(86400)
    def get_for_date(cls, date):
        try:
            return cls.objects.filter(Q(valid_until__gt=date) | Q(valid_until=None),
                                      valid_from__lte=date)[0]
        except IndexError:
            return None

    @classmethod
    @memoize(3600)
    def get_current(cls):
        return cls.get_for_date(datetime.now(timezone.utc))

    def get_previous_renewal(self, from_date):
        if not self.does_vote_eligibility_need_renewal:
            return self.valid_from

        dtstart = datetime(from_date.year - 1, from_date.month, 1) + relativedelta(months=1)
        return max(self.valid_from, rrule(YEARLY, dtstart=dtstart, bymonth=self.renewal_month, count=1)[0].date())

    def get_next_renewal(self, from_date):
        if not self.does_vote_eligibility_need_renewal:
            return self.valid_until or date.max

        dtstart = datetime(from_date.year, from_date.month, 1)
        return min(
            self.valid_until or date.max,
            rrule(YEARLY, dtstart=dtstart, bymonth=self.renewal_month, count=1)[0].date()
        )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        delete_memoized(self.__class__.get_last)
        delete_memoized(self.__class__.get_for_date)
        delete_memoized(self.__class__.get_current)
        delete_memoized(is_system_initialized)
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
    address = models.TextField(blank=True)
    postcode = models.TextField(blank=True)
    phone = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    participation_form_filled = models.DateField()

    @property
    def age(self):
        return relativedelta(datetime.now(timezone.utc).date(), self.date_of_birth).years

    @property
    def is_under_aged(self):
        return self.age < 18

    def __str__(self):
        return '{} {}'.format(self.name, self.surname)


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
    can_vote = models.BooleanField()
    needs_renewal = models.BooleanField()

    def is_usable_for(self, ref_date):
        return self.usable_from <= ref_date and (self.usable_until is None or self.usable_until >= ref_date)

    def __str__(self):
        return '{} ({} - {})'.format(self.name, self.usable_from, self.usable_until or '')


class MemberTypeTier(Loggable, models.Model):
    class MemberTypeTierManager(models.Manager):
        def get_queryset(self):
            return super(MemberTypeTier.MemberTypeTierManager, self).get_queryset().select_related()

    objects = MemberTypeTierManager()

    member_type = models.ForeignKey(MemberType, on_delete=models.PROTECT, related_name='membership_combinations')
    tier = models.ForeignKey(Tier, on_delete=models.PROTECT, related_name='membership_combinations')
    base_amount = models.PositiveIntegerField()

    def is_usable_for(self, ref_date):
        return self.tier.is_usable_for(ref_date)

    def __str__(self):
        return '{} {} ({})'.format(self.member_type, self.tier, self.base_amount)


class Membership(Loggable, models.Model):
    member_type = models.ForeignKey(MemberTypeTier, on_delete=models.PROTECT, related_name='memberships')
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name='memberships')
    effective_from = models.DateField()
    form_filled = models.DateField()
    paid = models.DateField(null=True, blank=True)
    amount_paid = models.PositiveIntegerField()
    payment_method = models.PositiveIntegerField(choices=PAYMENT_METHODS.items())
    is_renewal = models.BooleanField()
    notes = models.TextField(null=True, blank=True)

    def is_active_on(self, on_date, general_setup_ref=None):
        if isinstance(on_date, datetime):
            on_date = on_date.date()
        tier = self.member_type.tier
        if not tier.needs_renewal and tier.usable_from <= on_date < (tier.usable_until or date.max):
            return True

        setup = general_setup_ref or GeneralSetup.get_for_date(on_date)
        previous_renewal = setup.get_previous_renewal(on_date)
        if bool(tier.usable_until) and (previous_renewal < tier.usable_until < on_date):
            # If the tier is usable over the period of the setup, it means that Tier was allowed into the new period
            # keeping the rules of the old one, so override the setup to the previous period
            on_date = previous_renewal - timedelta(days=1)
            setup = GeneralSetup.get_for_date(on_date)
            previous_renewal = setup.get_previous_renewal(on_date)
        next_renewal = setup.get_next_renewal(on_date)
        return previous_renewal <= self.effective_from < next_renewal

    @property
    def is_active(self):
        return self.is_active_on(datetime.now(timezone.utc), GeneralSetup.get_current())

    def __str__(self):
        return '{} membership for {}'.format(self.effective_from, self.participant)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        try:
            last_membership = self.__class__.objects.filter(
                participant_id=self.participant_id
            ).order_by('-effective_from')[0]
        except IndexError:
            self.is_renewal = False
        else:
            # If it was active last month, this new Membership is a renewal
            self.is_renewal = last_membership.is_active_on(self.effective_from - relativedelta(months=1))

        super(Membership, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                     update_fields=update_fields)
