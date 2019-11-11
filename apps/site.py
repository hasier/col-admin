from material.admin.sites import MaterialAdminSite


class NoThemeMaterialAdminSite(MaterialAdminSite):
    def get_urls(self):
        return super().get_urls()[:-1]
