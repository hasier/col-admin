from datetime import datetime, timedelta, date

import pytest

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
