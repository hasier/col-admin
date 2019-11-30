from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.urls import include, path, re_path

urlpatterns = [
    path('admin/', include('material.admin.urls')),
    path('accounts/', include('allauth.urls')),
    path('invitations/', include('invitations.urls', namespace='invitations')),
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
