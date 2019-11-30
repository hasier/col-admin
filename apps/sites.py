from django.contrib.admin import site
from django.contrib.admin.sites import AlreadyRegistered
from django.db.models.base import ModelBase
from django.templatetags.static import static
from django.utils.translation import ugettext_lazy as _
from material.admin.options import MaterialModelAdmin
from material.admin.sites import MaterialAdminSite


class NoThemeMaterialAdminSite(MaterialAdminSite):
    site_header = _('Castellers of London')
    site_title = _('Castellers of London')
    favicon = static('CoL_Logo.png')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.default_icons = {
            'allauth.account.admin.EmailAddressAdmin': 'email',
            'invitations.admin.InvitationAdmin': 'send',
        }

    def get_urls(self):
        return super().get_urls()[:-1]

    def register(self, model_or_iterable, admin_class=None, **options):
        class_name = f'{admin_class.__module__}.{admin_class.__qualname__}'
        if class_name in self.default_icons:
            admin_class.icon_name = getattr(
                admin_class, 'icon_name', self.default_icons.get(class_name)
            )

        # Force overwriting models with their Material version
        try:
            super().register(model_or_iterable, admin_class=admin_class, **options)
        except AlreadyRegistered:
            if issubclass(admin_class, MaterialModelAdmin):
                if isinstance(model_or_iterable, ModelBase):
                    model_or_iterable = [model_or_iterable]
                for model in model_or_iterable:
                    self._registry.pop(model, None)
                super().register(model_or_iterable, admin_class=admin_class, **options)


def default_site_override():
    return site
