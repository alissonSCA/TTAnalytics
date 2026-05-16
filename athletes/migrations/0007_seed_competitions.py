from django.db import migrations


def seed_competitions(apps, schema_editor):
    Competition = apps.get_model('athletes', 'Competition')

    names = [
        'Campeonato Cearense',
        'Liga Metropolitana',
        'Copa IFCE Maranguape',
        'Torneio Interno do Clube',
    ]

    for name in names:
        Competition.objects.get_or_create(name=name)


def unseed_competitions(apps, schema_editor):
    Competition = apps.get_model('athletes', 'Competition')
    Competition.objects.filter(
        name__in=[
            'Campeonato Cearense',
            'Liga Metropolitana',
            'Copa IFCE Maranguape',
            'Torneio Interno do Clube',
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('athletes', '0006_competition_matchvideo'),
    ]

    operations = [
        migrations.RunPython(seed_competitions, reverse_code=unseed_competitions),
    ]
