from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Family',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('family_name', models.TextField()),
            ],
            options={
                'verbose_name_plural': 'families',
            },
        ),
        migrations.CreateModel(
            name='GeneralSetup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('valid_from', models.DateField(db_index=True)),
                ('time_to_vote_since_membership', models.PositiveIntegerField()),
                (
                    'time_unit_to_vote_since_membership',
                    models.PositiveIntegerField(choices=[(1, 'Days'), (2, 'Weeks'), (3, 'Months')]),
                ),
                ('minimum_age_to_vote', models.PositiveIntegerField()),
                ('renewal_month', models.PositiveIntegerField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MemberType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('type_name', models.TextField()),
                ('notes', models.TextField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Tier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('name', models.TextField()),
                ('usable_from', models.DateField()),
                ('usable_until', models.DateField(blank=True, null=True)),
                ('can_vote', models.BooleanField()),
                ('needs_renewal', models.BooleanField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Participant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('name', models.TextField()),
                ('surname', models.TextField()),
                ('date_of_birth', models.DateField()),
                ('participation_form_filled', models.DateField()),
                ('family', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                             related_name='family_members', to='col.Family')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MemberTypeTier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('base_amount', models.PositiveIntegerField()),
                (
                    'member_type',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='membership_combinations',
                        to='col.MemberType'
                    ),
                ),
                (
                    'tier',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='membership_combinations',
                        to='col.Tier',
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('effective_from', models.DateField()),
                ('effective_until', models.DateField(blank=True, null=True)),
                ('form_filled', models.DateField()),
                ('paid', models.DateField(blank=True, null=True)),
                ('amount_paid', models.PositiveIntegerField()),
                (
                    'payment_method',
                    models.PositiveIntegerField(choices=[(1, 'Cash'), (2, 'Bank transfer'), (3, 'SumUp')]),
                ),
                ('is_renewal', models.BooleanField()),
                ('notes', models.TextField(blank=True, null=True)),
                (
                    'member_type',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='memberships',
                        to='col.MemberTypeTier'
                    ),
                ),
                ('participant',
                 models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='memberships',
                                   to='col.Participant')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HealthInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('height', models.PositiveIntegerField(blank=True, null=True)),
                ('weight', models.PositiveIntegerField(blank=True, null=True)),
                ('info', models.TextField()),
                (
                    'participant',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='health_info',
                        to='col.Participant',
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EmergencyContact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('full_name', models.TextField()),
                ('phone', models.TextField()),
                ('relation', models.TextField()),
                (
                    'participant',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='emergency_contacts',
                        to='col.Participant',
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ContactInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
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
                        to='col.Participant',
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
