from datetime import timedelta, date

import factory
from django.utils import timezone
from factory import fuzzy

from apps.membership import models
from apps.membership.constants import TimeUnit, PaymentMethod


class GeneralSetupFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.GeneralSetup

    valid_from = date(2015, 1, 1)
    time_to_vote_since_membership = fuzzy.FuzzyInteger(low=1)
    time_unit_to_vote_since_membership = fuzzy.FuzzyChoice(choices=TimeUnit.choices())
    minimum_age_to_vote = fuzzy.FuzzyInteger(low=16)
    renewal_month = fuzzy.FuzzyInteger(low=1, high=12)


class ParticipantFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Participant

    name = fuzzy.FuzzyText()
    surname = fuzzy.FuzzyText()
    date_of_birth = fuzzy.FuzzyDate(start_date=(timezone.now() - timedelta(days=36500)).date())
    participation_form_filled_on = fuzzy.FuzzyDate(
        start_date=(timezone.now() - timedelta(days=365)).date()
    )


class MemberTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.MemberType

    type_name = fuzzy.FuzzyText()


class TierFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Tier

    name = fuzzy.FuzzyText()
    usable_from = fuzzy.FuzzyDate(start_date=(timezone.now() - timedelta(days=30)).date())
    member_type = factory.SubFactory(MemberTypeFactory)
    can_vote = True
    needs_renewal = False
    base_amount = fuzzy.FuzzyInteger(low=5)


class MembershipFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Membership

    participant = factory.SubFactory(ParticipantFactory)
    tier = factory.SubFactory(TierFactory)
    effective_from = fuzzy.FuzzyDate(start_date=(timezone.now() - timedelta(days=30)).date())
    form_filled = fuzzy.FuzzyDate(start_date=(timezone.now() - timedelta(days=30)).date())


class MembershipPaymentFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.MembershipPayment

    membership = factory.SubFactory(MembershipFactory)
    amount_paid = fuzzy.FuzzyInteger(low=5)
    payment_method = fuzzy.FuzzyChoice(dict(PaymentMethod.choices()).keys())
