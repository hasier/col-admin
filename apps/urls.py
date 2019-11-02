from django.templatetags.static import static
from django.urls import path, include
from django.utils.translation import ugettext_lazy as _
from material.admin.sites import site

site.site_header = _('Castellers of London')
site.site_title = _('Castellers of London')
site.favicon = static('CoL_Logo.png')

urlpatterns = [
    path('', include('apps.login.urls')),
]
