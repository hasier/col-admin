from django.db.models import DurationField as DjangoDurationField


class DurationField(DjangoDurationField):
    def get_placeholder(self, value, compiler, connection):
        return '%s::INTERVAL'
