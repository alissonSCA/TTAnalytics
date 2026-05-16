from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('athletes', '0004_remove_club_abbreviation_club_short_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='athleteprofile',
            old_name='age',
            new_name='birth_year',
        ),
        migrations.AlterField(
            model_name='athleteprofile',
            name='birth_year',
            field=models.PositiveSmallIntegerField(
                validators=[MinValueValidator(1900), MaxValueValidator(2100)],
                verbose_name='Ano de nascimento',
            ),
        ),
    ]
