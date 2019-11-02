from datetime import timedelta
from typing import Union

from dateutil.relativedelta import relativedelta

from apps.membership.constants import TimeUnit


def get_timedelta_from_unit(time_diff: int, unit: str) -> Union[timedelta, relativedelta]:
    unit = TimeUnit.get_from_value(unit)
    if unit == TimeUnit.DAYS:
        return timedelta(days=time_diff)

    return relativedelta(**{unit.value.lower(): time_diff})
