# Generated by Django 4.0.3 on 2022-12-19 10:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0011_remove_salotherincomes_rent_reflection_in_bank'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='saladditionalotherincomes',
            name='other_income',
        ),
        migrations.AddField(
            model_name='saladditionalotherincomes',
            name='Future_Rent',
            field=models.BooleanField(choices=[(None, 'Select Yes Or No'), (True, 'Yes'), (False, 'No')], default=1),
            preserve_default=False,
        ),
    ]
