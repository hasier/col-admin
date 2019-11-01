from datetime import timedelta

from dateutil.relativedelta import relativedelta

from apps.membership.constants import TimeUnit


def get_timedelta_from_unit(time_diff, unit):
    unit = TimeUnit(unit)
    if unit == TimeUnit.DAYS:
        return timedelta(days=time_diff)

    return relativedelta(**{unit.value.lower(): time_diff})
