import enum

from contrib.enum import ChoiceEnumMixin


class PaymentMethod(ChoiceEnumMixin, enum.Enum):
    PAYMENT_METHOD_CASH = 'Cash'
    PAYMENT_METHOD_TRANSFER = 'Bank transfer'
    PAYMENT_METHOD_SUMUP = 'SumUp'


class TimeUnit(ChoiceEnumMixin, enum.Enum):
    DAYS = 'Days'
    WEEKS = 'Weeks'
    MONTHS = 'Months'
