from datetime import date

import pytest

from apps.membership import models
from apps.membership.constants import TimeUnit
from apps.membership.filters import EligibleForVoteParticipantFilter
from apps.membership.tests import factories


@pytest.mark.django_db
@pytest.mark.parametrize('create_general_setup', [True, False])
@pytest.mark.parametrize(
    ['invalid_date_format'],
    [('%d-%m-%Y',), ('%m-%d-%Y',), ('%m/%d/%Y',), ('%Y/%m/%d',), ('%Y-%m-%d',)],
)
def test_eligible_for_vote_filter_fails(create_general_setup, invalid_date_format):
    if create_general_setup:
        factories.GeneralSetupFactory(valid_from=date(2015, 1, 1))

    vote_filter = EligibleForVoteParticipantFilter(
        request=None,
        params={
            EligibleForVoteParticipantFilter.parameter_name: date(2019, 11, 1).strftime(
                invalid_date_format
            )
        },
        model=None,
        model_admin=None,
    )

    vote_filter_qs = vote_filter.queryset(None, models.Participant.objects.all())
    assert list(vote_filter_qs) == []


def test_eligible_for_vote_filter_no_value():
    vote_filter = EligibleForVoteParticipantFilter(
        request=None,
        params={EligibleForVoteParticipantFilter.parameter_name: None},
        model=None,
        model_admin=None,
    )

    qs = models.Participant.objects.all()
    vote_filter_qs = vote_filter.queryset(None, qs)
    assert vote_filter_qs is qs


@pytest.mark.django_db
@pytest.mark.parametrize(
    ['vote_date', 'is_id_expected'],
    [
        (date(2019, 2, 8), False),
        (date(2020, 2, 7), False),
        (date(2020, 2, 8), True),
        (date(2020, 12, 31), True),
        (date(2021, 1, 1), False),
    ],
)
def test_eligible_for_vote_filter_full_pass(vote_date, is_id_expected):
    factories.GeneralSetupFactory(
        valid_from=date(2015, 1, 1),
        time_to_vote_since_membership=3,
        time_unit_to_vote_since_membership=TimeUnit.MONTHS.value,
        minimum_age_to_vote=18,
        renewal_month=1,
    )
    participant = factories.ParticipantFactory(date_of_birth=date(1990, 12, 1))

    tier = factories.TierFactory(needs_renewal=True, usable_from=date(2015, 1, 1))
    membership = factories.MembershipFactory(
        participant=participant,
        tier=tier,
        effective_from=date(2019, 11, 8),
        form_filled=date(2019, 11, 8),
    )
    assert membership.effective_until == date(2019, 12, 31)
    membership = factories.MembershipFactory(
        participant=participant,
        tier=tier,
        effective_from=date(2020, 1, 1),
        form_filled=date(2020, 1, 1),
    )
    assert membership.effective_until == date(2020, 12, 31)

    vote_filter = EligibleForVoteParticipantFilter(
        request=None,
        params={EligibleForVoteParticipantFilter.parameter_name: vote_date.strftime('%d/%m/%Y')},
        model=None,
        model_admin=None,
    )

    vote_filter_qs = vote_filter.queryset(None, models.Participant.objects.all())
    assert (participant in list(vote_filter_qs)) is is_id_expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    ['vote_date', 'is_id_expected'],
    [
        (date(2019, 2, 8), False),
        (date(2020, 2, 7), False),
        (date(2020, 2, 8), False),
        (date(2020, 4, 30), False),
        (date(2020, 5, 1), True),
        (date(2020, 12, 31), True),
        (date(2021, 1, 1), False),
    ],
)
def test_eligible_for_vote_filter_gaps_pass(vote_date, is_id_expected):
    factories.GeneralSetupFactory(
        valid_from=date(2015, 1, 1),
        time_to_vote_since_membership=3,
        time_unit_to_vote_since_membership=TimeUnit.MONTHS.value,
        minimum_age_to_vote=18,
        renewal_month=1,
    )
    participant = factories.ParticipantFactory(date_of_birth=date(1990, 12, 1))

    tier = factories.TierFactory(needs_renewal=True, usable_from=date(2015, 1, 1))
    membership = factories.MembershipFactory(
        participant=participant,
        tier=tier,
        effective_from=date(2019, 11, 8),
        form_filled=date(2019, 11, 8),
    )
    assert membership.effective_until == date(2019, 12, 31)
    membership = factories.MembershipFactory(
        participant=participant,
        tier=tier,
        effective_from=date(2020, 2, 1),
        form_filled=date(2020, 2, 1),
    )
    assert membership.effective_until == date(2020, 12, 31)

    vote_filter = EligibleForVoteParticipantFilter(
        request=None,
        params={EligibleForVoteParticipantFilter.parameter_name: vote_date.strftime('%d/%m/%Y')},
        model=None,
        model_admin=None,
    )

    vote_filter_qs = vote_filter.queryset(None, models.Participant.objects.all())
    assert (participant in list(vote_filter_qs)) is is_id_expected
