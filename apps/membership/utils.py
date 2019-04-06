from datetime import timedelta

from dateutil.relativedelta import relativedelta

from apps.membership.constants import DAYS, TIME_UNIT_CHOICES


def get_timedelta_from_unit(time_diff, unit):
    if unit == DAYS:
        return timedelta(days=time_diff)

    time_unit = TIME_UNIT_CHOICES[unit]
    return relativedelta(**{time_unit.lower(): time_diff})