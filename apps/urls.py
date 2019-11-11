from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.templatetags.static import static
from django.urls import include, path, re_path
from django.utils.translation import ugettext_lazy as _
from material.admin.sites import site

site.site_header = _('Castellers of London')
site.site_title = _('Castellers of London')
site.favicon = static('CoL_Logo.png')

urlpatterns = [
    path('admin/', include('material.admin.urls')),
    re_path(r'^admin/password_reset/$', PasswordResetView.as_view(), name='admin_password_reset'),
    re_path(
        r'^admin/password_reset/done/$',
        PasswordResetDoneView.as_view(),
        name='password_reset_done',
    ),
    re_path(
        r'^admin/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        PasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    re_path(
        r'^admin/reset/done/$', PasswordResetCompleteView.as_view(), name='password_reset_complete'
    ),
]
