from material.admin.sites import MaterialAdminSite


class NoThemeMaterialAdminSite(MaterialAdminSite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.default_config_mapping = {
            **self.default_config_mapping,
            **{
                'auth': 'lock',
                'invitations': 'send',
                'account': 'account_circle',
                'socialaccount': 'wifi_tethering',
            },
        }
        self.model_icon_mapping = {
            **self.model_icon_mapping,
            **{'invitation': 'send', 'emailaddress': 'email'},
        }

    def get_urls(self):
        return super().get_urls()[:-1]
