from datetime import datetime, timedelta

import pytest

from apps.membership import models
from apps.membership.tests import factories

pytestmark = pytest.mark.django_db


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
