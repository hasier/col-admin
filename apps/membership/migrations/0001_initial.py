# Generated by Django 2.2.6 on 2019-11-16 12:21
from datetime import date

import django.db.models.deletion
from django.db import migrations, models
from django.utils.dates import MONTHS

from apps.membership.constants import PaymentMethod, TimeUnit


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Family',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('family_name', models.TextField()),
            ],
            options={'verbose_name_plural': 'families'},
        ),
        migrations.CreateModel(
            name='GeneralSetup',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('valid_from', models.DateField(db_index=True)),
                ('time_to_vote_since_membership', models.PositiveIntegerField()),
                (
                    'time_unit_to_vote_since_membership',
                    models.TextField(choices=TimeUnit.choices()),
                ),
                ('minimum_age_to_vote', models.PositiveIntegerField()),
                (
                    'renewal_month',
                    models.PositiveIntegerField(
                        blank=True, null=True, choices=sorted(MONTHS.items())
                    ),
                ),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='MemberType',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('type_name', models.TextField()),
                ('notes', models.TextField(blank=True, null=True)),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='Tier',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('name', models.TextField()),
                ('usable_from', models.DateField()),
                ('usable_until', models.DateField(blank=True, null=True)),
                ('can_vote', models.BooleanField()),
                ('needs_renewal', models.BooleanField()),
                ('base_amount', models.PositiveIntegerField()),
                (
                    'member_type',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='tiers',
                        to='membership.MemberType',
                    ),
                ),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='Participant',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('name', models.TextField()),
                ('surname', models.TextField()),
                ('date_of_birth', models.DateField()),
                ('participation_form_filled_on', models.DateField()),
                (
                    'family',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='family_members',
                        to='membership.Family',
                    ),
                ),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('effective_from', models.DateField()),
                ('effective_until', models.DateField(blank=True, null=True)),
                ('form_filled', models.DateField()),
                ('paid_on', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                (
                    'participant',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='memberships',
                        to='membership.Participant',
                    ),
                ),
                (
                    'tier',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='memberships',
                        to='membership.Tier',
                    ),
                ),
            ],
            options={'abstract': False},
        ),
        migrations.AddField(
            model_name='membership',
            name='group_first_membership',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='grouped_memberships',
                to='membership.Membership',
            ),
        ),
        migrations.CreateModel(
            name='MembershipPayment',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('amount_paid', models.PositiveIntegerField()),
                ('payment_method', models.TextField(choices=PaymentMethod.choices()),),
                (
                    'membership',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='payments',
                        to='membership.Membership',
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='HealthInfo',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('height', models.PositiveIntegerField()),
                ('weight', models.PositiveIntegerField(blank=True, null=True)),
                ('info', models.TextField(blank=True, null=True)),
                (
                    'participant',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='health_info',
                        to='membership.Participant',
                    ),
                ),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='EmergencyContact',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('full_name', models.TextField()),
                ('phone', models.TextField()),
                ('relation', models.TextField()),
                (
                    'participant',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='emergency_contacts',
                        to='membership.Participant',
                    ),
                ),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='ContactInfo',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('address', models.TextField(blank=True)),
                ('postcode', models.TextField(blank=True)),
                ('phone', models.TextField(blank=True)),
                ('email', models.EmailField(blank=True, max_length=254)),
                (
                    'participant',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='contact_info',
                        to='membership.Participant',
                    ),
                ),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='MembershipPeriod',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('can_vote', models.BooleanField()),
                ('effective_from', models.DateField()),
                ('effective_until', models.DateField()),
            ],
            options={'db_table': 'membership_membershipperiod', 'managed': False},
        ),
        migrations.RunSQL(
            sql=[
                (
                    '''CREATE OR REPLACE VIEW 
                       membership_membershipperiod AS
                       SELECT
                           row_number() OVER (PARTITION BY TRUE) AS id,
                           MIN(m.effective_from) AS effective_from, 
                           MAX(COALESCE(m.effective_until, %(max_date)s)) AS effective_until,
                           -- participant_id should be consistent for the group anyway
                           MAX(m.participant_id) AS participant_id
                       FROM membership_membership AS m
                           JOIN membership_tier AS t ON m.tier_id = t.id
                       GROUP BY COALESCE(m.group_first_membership_id, m.id)''',
                    dict(max_date=date.max.isoformat()),
                )
            ],
            reverse_sql='DROP VIEW IF EXISTS membership_membershipperiod',
        ),
    ]
