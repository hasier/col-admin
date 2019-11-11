from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
from django.utils.translation import ugettext_lazy as _


class UserManager(DjangoUserManager):
    def _create_user(self, username, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        return super()._create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    class Meta:
        db_table = 'auth_user'

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[AbstractUser.username_validator],
        error_messages={'unique': _("A user with that username already exists."),},
        editable=False,
    )
    email = models.EmailField(_('email address'), unique=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not update_fields or 'username' in update_fields or 'email' in update_fields:
            self.username = self.email
        return super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
