from django.db.models.signals import post_save
from memoize import delete_memoized

from apps.membership.templatetags.membership import is_membership_setup_initialized


def invalidate_general_setup(sender, **kwargs):
    delete_memoized(sender.get_last)
    delete_memoized(sender.get_for_date)
    delete_memoized(sender.get_current)
    delete_memoized(sender.get_next)
    delete_memoized(sender.get_previous)
    delete_memoized(is_membership_setup_initialized)


def setup():
    from . import models

    post_save.connect(invalidate_general_setup, sender=models.GeneralSetup)
