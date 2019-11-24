from datetime import datetime, timedelta, date

import pytest
from django.core.exceptions import ValidationError
from freezegun import freeze_time

from apps.membership import models
from apps.membership.tests import factories

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clear_memoize():
    yield
    models.GeneralSetup.get_last.delete_memoized()
    models.GeneralSetup.get_for_date.delete_memoized()
    models.GeneralSetup.get_current.delete_memoized()
    models.GeneralSetup.get_next.delete_memoized()
    models.GeneralSetup.get_previous.delete_memoized()


@pytest.fixture
def usable_from():
    return date(2019, 1, 1)


class RequiresGeneralSetup:
    @pytest.fixture(autouse=True)
    def general_setup(self):
        return factories.GeneralSetupFactory(valid_from=date(2015, 1, 1), renewal_month=1)


class TestGeneralSetup:
    def test_get_last_empty(self):
        assert models.GeneralSetup.get_last() is None

    def test_get_last_pass(self):
        now = datetime.utcnow()
        setup = factories.GeneralSetupFactory(valid_from=now)
        factories.GeneralSetupFactory(valid_from=now - timedelta(days=30))
        assert models.GeneralSetup.get_last() == setup

    def test_get_for_date_empty(self):
        assert models.GeneralSetup.get_for_date(datetime.utcnow()) is None

    def test_get_for_date_pass(self):
        now = datetime.utcnow()
        setup1 = factories.GeneralSetupFactory(valid_from=now - timedelta(days=30))
        setup2 = factories.GeneralSetupFactory(valid_from=now)
        setup3 = factories.GeneralSetupFactory(valid_from=now + timedelta(days=15))
        assert models.GeneralSetup.get_for_date(now - timedelta(days=31)) is None
        assert models.GeneralSetup.get_for_date(now - timedelta(days=15)) == setup1
        assert models.GeneralSetup.get_for_date(datetime.utcnow()) == setup2
        assert models.GeneralSetup.get_for_date(datetime.utcnow() + timedelta(days=30)) == setup3

    def test_get_current_empty(self):
        assert models.GeneralSetup.get_current() is None

    def test_get_current_pass(self):
        now = datetime.utcnow()
        factories.GeneralSetupFactory(valid_from=now + timedelta(days=30))
        setup = factories.GeneralSetupFactory(valid_from=now)
        factories.GeneralSetupFactory(valid_from=now - timedelta(days=30))
        assert models.GeneralSetup.get_current() == setup

    def test_get_next_empty(self):
        assert models.GeneralSetup.get_next(datetime.utcnow()) is None

    def test_get_next_pass(self):
        now = datetime.utcnow()
        setup1 = factories.GeneralSetupFactory(valid_from=now - timedelta(days=30))
        setup2 = factories.GeneralSetupFactory(valid_from=now)
        setup3 = factories.GeneralSetupFactory(valid_from=now + timedelta(days=15))
        assert models.GeneralSetup.get_next(now - timedelta(days=31)) == setup1
        assert models.GeneralSetup.get_next(now - timedelta(days=15)) == setup2
        assert models.GeneralSetup.get_next(datetime.utcnow()) == setup3
        assert models.GeneralSetup.get_next(datetime.utcnow() + timedelta(days=30)) is None

    @pytest.mark.parametrize(
        ['month', 'expected_date'],
        [
            (1, date(2019, 1, 1)),
            (2, date(2019, 2, 1)),
            (3, date(2019, 3, 1)),
            (4, date(2019, 4, 1)),
            (5, date(2019, 5, 1)),
            (6, date(2019, 6, 1)),
            (7, date(2019, 7, 1)),
            (8, date(2019, 8, 1)),
            (9, date(2019, 9, 1)),
            (10, date(2019, 10, 1)),
            (11, date(2019, 11, 1)),
            (12, date(2019, 12, 1)),
        ],
    )
    def test_get_previous_renewal_single(self, month, expected_date):
        setup = factories.GeneralSetupFactory(valid_from=date(2017, 1, 1), renewal_month=month)
        assert setup.get_previous_renewal(datetime(2020, 1, 1)) == expected_date

    @pytest.mark.parametrize(
        ['month', 'expected_date'],
        [
            (1, date(2016, 7, 1)),
            (2, date(2016, 7, 1)),
            (3, date(2016, 7, 1)),
            (4, date(2016, 7, 1)),
            (5, date(2016, 7, 1)),
            (6, date(2016, 7, 1)),
            (7, date(2016, 7, 1)),
            (8, date(2016, 8, 1)),
            (9, date(2016, 9, 1)),
            (10, date(2016, 10, 1)),
            (11, date(2016, 11, 1)),
            (12, date(2016, 12, 1)),
        ],
    )
    def test_get_previous_renewal_multiple(self, month, expected_date):
        setup = factories.GeneralSetupFactory(valid_from=date(2017, 1, 1), renewal_month=month)
        factories.GeneralSetupFactory(valid_from=date(2015, 6, 1), renewal_month=7)
        assert setup.get_previous_renewal(datetime(2017, 1, 1)) == expected_date

    @pytest.mark.parametrize(
        ['month', 'expected_date'],
        [
            (1, date(2020, 1, 1)),
            (2, date(2020, 2, 1)),
            (3, date(2020, 3, 1)),
            (4, date(2020, 4, 1)),
            (5, date(2020, 5, 1)),
            (6, date(2020, 6, 1)),
            (7, date(2020, 7, 1)),
            (8, date(2020, 8, 1)),
            (9, date(2020, 9, 1)),
            (10, date(2020, 10, 1)),
            (11, date(2020, 11, 1)),
            (12, date(2020, 12, 1)),
        ],
    )
    def test_get_next_renewal_single(self, month, expected_date):
        setup = factories.GeneralSetupFactory(valid_from=date(2017, 1, 1), renewal_month=month)
        assert setup.get_next_renewal(datetime(2019, 12, 1)) == expected_date

    @pytest.mark.parametrize(
        ['month', 'expected_date'],
        [
            (1, date(2020, 1, 1)),
            (2, date(2020, 2, 1)),
            (3, date(2020, 3, 1)),
            (4, date(2020, 4, 1)),
            (5, date(2020, 5, 1)),
            (6, date(2020, 6, 1)),
            (7, date(2020, 7, 1)),
            (8, date(2020, 7, 1)),
            (9, date(2020, 7, 1)),
            (10, date(2020, 7, 1)),
            (11, date(2020, 7, 1)),
            (12, date(2020, 7, 1)),
        ],
    )
    def test_get_next_renewal_multiple(self, month, expected_date):
        setup = factories.GeneralSetupFactory(valid_from=date(2017, 1, 1), renewal_month=month)
        factories.GeneralSetupFactory(valid_from=date(2020, 6, 1), renewal_month=7)
        assert setup.get_next_renewal(datetime(2019, 12, 1)) == expected_date


class TestParticipant(RequiresGeneralSetup):
    @pytest.mark.parametrize(
        ['date_of_birth', 'age', 'is_under_aged'],
        [
            (date(2001, 12, 1), 17, True),
            (date(2001, 11, 1), 18, False),
            (date(2002, 1, 1), 17, True),
            (date(1991, 12, 1), 27, False),
        ],
    )
    @freeze_time(time_to_freeze=datetime(2019, 11, 1))
    def test_age(self, date_of_birth, age, is_under_aged):
        participant = factories.ParticipantFactory(date_of_birth=date_of_birth)
        assert participant.age == age
        assert participant.is_under_aged is is_under_aged


class TestTier(RequiresGeneralSetup):
    @pytest.mark.parametrize(
        ['usable_from', 'usable_until', 'expected_result'],
        [
            # In range
            (date(2019, 1, 1), None, True),
            (date(2019, 1, 1), date(2020, 1, 1), True),
            (date(2019, 11, 1), None, True),
            (date(2019, 11, 1), date(2020, 11, 1), True),
            # Future
            (date(2020, 1, 1), None, False),
            (date(2020, 1, 1), date(2020, 11, 1), False),
            # Past
            (date(2018, 1, 1), date(2019, 10, 1), False),
            (date(2018, 1, 1), date(2019, 11, 1), False),
        ],
    )
    def test_is_usable_for(self, usable_from, usable_until, expected_result):
        tier = factories.TierFactory(usable_from=usable_from, usable_until=usable_until)
        assert tier.is_usable_for(datetime(2019, 11, 1)) is expected_result


class TestMembership(RequiresGeneralSetup):
    @pytest.mark.parametrize(['amounts', 'expected'], [([5, 7], 12), ([5, 7, 12], 24), ([10], 10)])
    def test_amount_paid(self, amounts, expected):
        membership = factories.MembershipFactory()
        for amount in amounts:
            factories.MembershipPaymentFactory(membership=membership, amount_paid=amount)

        assert membership.amount_paid == expected

    @pytest.mark.parametrize(
        ['effective_from', 'effective_until', 'expected_result'],
        [
            # In range
            (date(2019, 1, 1), None, True),
            (date(2019, 1, 1), date(2020, 1, 1), True),
            (date(2019, 11, 1), None, True),
            (date(2019, 11, 1), date(2020, 11, 1), True),
            # Future
            (date(2020, 1, 1), None, False),
            (date(2020, 1, 1), date(2020, 11, 1), False),
            # Past
            (date(2018, 1, 1), date(2019, 10, 1), False),
            (date(2018, 1, 1), date(2019, 11, 1), False),
        ],
    )
    def test_is_active_on(self, effective_from, effective_until, expected_result):
        membership = factories.MembershipFactory(
            effective_from=effective_from, effective_until=effective_until
        )
        assert membership.is_active_on(datetime(2019, 11, 1)) is expected_result

    @pytest.mark.parametrize(
        ['effective_from', 'effective_until', 'expected_result'],
        [
            # In range
            (date(2019, 1, 1), None, True),
            (date(2019, 1, 1), date(2020, 1, 1), True),
            (date(2019, 11, 1), None, True),
            (date(2019, 11, 1), date(2020, 11, 1), True),
            # Future
            (date(2020, 1, 1), None, False),
            (date(2020, 1, 1), date(2020, 11, 1), False),
            # Past
            (date(2018, 1, 1), date(2019, 10, 1), False),
            (date(2018, 1, 1), date(2019, 11, 1), False),
        ],
    )
    @freeze_time(time_to_freeze=datetime(2019, 11, 1))
    def test_is_active(self, effective_from, effective_until, expected_result):
        membership = factories.MembershipFactory(
            effective_from=effective_from, effective_until=effective_until
        )
        assert membership.is_active is expected_result

    @pytest.mark.parametrize(
        ['renewing_tier', 'expected_until'], [(True, date(2020, 1, 1)), (False, None)]
    )
    def test_save_new(self, usable_from, renewing_tier, expected_until):
        membership = models.Membership.objects.create(
            participant=factories.ParticipantFactory(),
            tier=factories.TierFactory(needs_renewal=renewing_tier, usable_from=usable_from),
            effective_from=date(2019, 11, 1),
            form_filled=date(2019, 11, 1),
        )
        assert membership.effective_until == expected_until
        assert membership.renewed_membership is None

    @pytest.mark.parametrize(
        ['renewing_tier_previous', 'renewing_tier_new'],
        [(True, True), (True, False), (False, True), (False, False)],
    )
    def test_save_existing(self, usable_from, renewing_tier_previous, renewing_tier_new):
        participant = factories.ParticipantFactory()
        previous_membership = factories.MembershipFactory(
            participant=participant,
            tier=factories.TierFactory(
                needs_renewal=renewing_tier_previous, usable_from=usable_from - timedelta(days=30)
            ),
            effective_from=date(2019, 1, 1),
        )
        with pytest.raises(ValidationError) as exc:
            models.Membership.objects.create(
                participant=participant,
                tier=factories.TierFactory(
                    needs_renewal=renewing_tier_new, usable_from=usable_from
                ),
                effective_from=date(2019, 11, 1),
                form_filled=date(2019, 11, 1),
            )

        err = exc.value
        assert isinstance(err, ValidationError)
        assert isinstance(err.error_dict.get('effective_from'), list)
        assert err.message_dict['effective_from'][0] == (
            'Cannot create a new membership until the previous one '
            f'({previous_membership}) has been closed'
        )

    @pytest.mark.parametrize(
        ['renewing_tier_previous', 'renewing_tier_new', 'expected_until'],
        [
            (True, True, date(2021, 1, 1)),
            (True, False, None),
            (False, True, date(2021, 1, 1)),
            (False, False, None),
        ],
    )
    def test_save_link_previous(
        self, usable_from, renewing_tier_previous, renewing_tier_new, expected_until
    ):
        participant = factories.ParticipantFactory()
        previous_membership = factories.MembershipFactory(
            participant=participant,
            tier=factories.TierFactory(
                needs_renewal=renewing_tier_previous, usable_from=usable_from
            ),
            effective_from=date(2019, 1, 1),
            effective_until=date(2020, 1, 1),
        )
        membership = models.Membership.objects.create(
            participant=participant,
            tier=factories.TierFactory(needs_renewal=renewing_tier_new, usable_from=usable_from),
            effective_from=date(2020, 1, 1),
            form_filled=date(2019, 11, 1),
        )

        assert membership.effective_until == expected_until
        assert membership.renewed_membership == previous_membership
