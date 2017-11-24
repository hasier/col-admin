from django.db import models
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from col.constants import PAYMENT_METHODS


class Loggable(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class GeneralSetup(Loggable, models.Model):
    valid_from = models.DateField()  # TODO Add validation on clean to ensure no overlap and no period uncovered
    valid_until = models.DateField()
    days_to_vote_since_membership = models.IntegerField()
    renewal_month = models.IntegerField()
    renewal_grace_months_period = models.IntegerField()


class Family(Loggable, models.Model):
    family_name = models.TextField()


class Participant(Loggable, models.Model):
    name = models.TextField()
    surname = models.TextField()
    date_of_birth = models.DateField()
    # TODO If age < 18, add validation on clean to ensure family != None and there are adults in family
    family = models.ForeignKey(Family, null=True, on_delete=models.PROTECT, related_name='family_members')
    # TODO If age > 18, add validation on clean to ensure these fields are not blank
    address = models.TextField(blank=True)
    postcode = models.TextField(blank=True)
    phone = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    participation_form_filled = models.DateField()
    # TODO Make sure we can enforce having at least one EmergencyContact

    @property
    def age(self):
        return relativedelta(datetime.now(timezone.utc), self.date_of_birth).years


class HealthInfo(Loggable, models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name='health_info')
    height = models.IntegerField(null=True)
    weight = models.IntegerField(null=True)
    info = models.TextField()


class EmergencyContact(Loggable, models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name='emergency_contacts')
    name = models.TextField()
    phone = models.TextField()
    relation = models.TextField()


class Tier(models.Model):
    name = models.TextField()
    base_amount = models.IntegerField()
    usable_from = models.DateField()
    usable_until = models.DateField(null=True)
    can_vote = models.BooleanField()

    def is_usable_for(self, year):
        return self.usable_from.year <= year and (self.usable_until is None or self.usable_until.year >= year)


class Membership(Loggable, models.Model):
    # TODO Add validation on clean to disable creation if < days_to_vote_since_membership
    tier = models.ForeignKey(Tier, on_delete=models.PROTECT, related_name='memberships')
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name='memberships')
    effective_for_year = models.IntegerField()  # TODO Add validation on clean to check it matches with tier
    form_filled = models.DateField()
    paid = models.DateField()
    amount_paid = models.IntegerField()
    payment_method = models.IntegerField(choices=PAYMENT_METHODS.items())
