from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta
from django.db import models
from memoize import delete_memoized, memoize

from col.constants import PAYMENT_METHODS


class Loggable(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class GeneralSetup(Loggable, models.Model):
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    days_to_vote_since_membership = models.PositiveIntegerField()
    days_before_vote_to_close_eligible_members = models.PositiveIntegerField()
    minimum_age_to_vote = models.PositiveIntegerField()
    does_vote_eligibility_need_renewal = models.BooleanField()
    renewal_month = models.PositiveIntegerField(null=True, blank=True)
    renewal_grace_months_period = models.PositiveIntegerField(null=True, blank=True)

    @classmethod
    @memoize(3600)
    def get_last(cls):
        try:
            return cls.objects.order_by('-created_at')[0]
        except KeyError:
            return None

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        delete_memoized(self.get_last)
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
    base_amount = models.PositiveIntegerField()
    usable_from = models.DateField()
    usable_until = models.DateField(null=True, blank=True)
    can_vote = models.BooleanField()
    needs_renewal = models.BooleanField()
    allowed_member_types = models.ManyToManyField(MemberType)

    def is_usable_for(self, ref_date):
        return self.usable_from <= ref_date and (self.usable_until is None or self.usable_until >= ref_date)

    def __str__(self):
        return self.name


class Membership(Loggable, models.Model):
    tier = models.ForeignKey(Tier, on_delete=models.PROTECT, related_name='memberships')
    member_type = models.ForeignKey(MemberType, on_delete=models.PROTECT, related_name='memberships')
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name='memberships')
    effective_from = models.DateField()
    form_filled = models.DateField()
    paid = models.DateField(null=True, blank=True)
    amount_paid = models.PositiveIntegerField()
    payment_method = models.PositiveIntegerField(choices=PAYMENT_METHODS.items())
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return '{} membership for {}'.format(self.effective_from, self.participant)
