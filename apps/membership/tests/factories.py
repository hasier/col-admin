from datetime import timedelta

import factory
from django.utils import timezone
from factory import fuzzy

from apps.membership import models
from apps.membership.constants import TimeUnit


class GeneralSetupFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.GeneralSetup

    valid_from = fuzzy.FuzzyDateTime(start_dt=timezone.now() - timedelta(days=30))
    time_to_vote_since_membership = fuzzy.FuzzyInteger(low=1)
    time_unit_to_vote_since_membership = fuzzy.FuzzyChoice(choices=TimeUnit.choices())
    minimum_age_to_vote = fuzzy.FuzzyInteger(low=16)
    renewal_month = fuzzy.FuzzyInteger(low=1, high=12)


class ParticipantFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Participant

    name = fuzzy.FuzzyText()
    surname = fuzzy.FuzzyText()
    date_of_birth = fuzzy.FuzzyDateTime(start_dt=timezone.now() - timedelta(days=36500))
    participation_form_filled_on = fuzzy.FuzzyDateTime(
        start_dt=timezone.now() - timedelta(days=365)
    )
