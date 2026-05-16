from django.db import migrations


def rename_point_markers(apps, schema_editor):
    MatchMarkerType = apps.get_model('athletes', 'MatchMarkerType')
    MatchMarkerType.objects.filter(code='point_my').update(name='Ponto Jogador 1')
    MatchMarkerType.objects.filter(code='point_opponent').update(name='Ponto Jogador 2')


class Migration(migrations.Migration):

    dependencies = [
        ('athletes', '0014_add_marker_details_and_rename_rebatida'),
    ]

    operations = [
        migrations.RunPython(rename_point_markers, reverse_code=migrations.RunPython.noop),
    ]