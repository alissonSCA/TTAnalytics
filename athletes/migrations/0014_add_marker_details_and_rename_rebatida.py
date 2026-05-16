from django.db import migrations, models


def rename_rebatida_marker(apps, schema_editor):
    MatchMarkerType = apps.get_model('athletes', 'MatchMarkerType')
    MatchMarkerType.objects.filter(code='first_to_fifth_ball').update(name='Rebatida')


class Migration(migrations.Migration):

    dependencies = [
        ('athletes', '0013_normalize_marker_shortcuts'),
    ]

    operations = [
        migrations.AddField(
            model_name='matchgameaction',
            name='detail_effect',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name='matchgameaction',
            name='detail_number',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='matchgameaction',
            name='detail_position',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.RunPython(rename_rebatida_marker, reverse_code=migrations.RunPython.noop),
    ]
