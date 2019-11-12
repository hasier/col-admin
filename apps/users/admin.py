from django.contrib.auth import admin, forms
from django.forms.fields import EmailField
from django.utils.translation import ugettext_lazy as _
from material.admin.options import MaterialModelAdmin
from material.admin.sites import site

from apps.users import models


class UserCreationForm(forms.UserCreationForm):
    email = EmailField(label=_("Email"))

    class Meta(forms.UserCreationForm.Meta):
        exclude = '__all__'
        fields = None
        field_classes = None


class UserAdmin(MaterialModelAdmin, admin.UserAdmin):
    icon_name = 'person'

    add_form = UserCreationForm
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (
            _('Permissions'),
            {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),},
        ),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2'),}),
    )


site.register(models.User, UserAdmin)
