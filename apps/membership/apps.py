from django.apps import AppConfig


class MembershipConfig(AppConfig):
    name = 'apps.membership'
    icon_name = 'card_membership'

    def ready(self):
        from . import signal_receivers

        signal_receivers.setup()
