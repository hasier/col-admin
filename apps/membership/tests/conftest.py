import pytest

from apps.membership import models


@pytest.fixture(autouse=True)
def clear_memoize():
    yield
    models.GeneralSetup.get_last.delete_memoized()
    models.GeneralSetup.get_for_date.delete_memoized()
    models.GeneralSetup.get_current.delete_memoized()
    models.GeneralSetup.get_next.delete_memoized()
    models.GeneralSetup.get_previous.delete_memoized()
