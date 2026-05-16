from django.db import migrations


FALLBACK_SHORTCUTS = {
    'start_game': 'S',
    'first_to_fifth_ball': 'B',
    'point_my': 'M',
    'point_opponent': 'O',
    'technical_timeout': 'T',
    'pause_restart': 'P',
    'start_set': 'I',
    'end_set': 'F',
    'end_game': 'G',
}


def normalize_marker_shortcuts(apps, schema_editor):
    MatchMarkerType = apps.get_model('athletes', 'MatchMarkerType')

    for marker in MatchMarkerType.objects.all():
        shortcut_key = marker.shortcut_key
        if shortcut_key:
            shortcut_key = shortcut_key.upper()

        if not shortcut_key or shortcut_key.isdigit():
            shortcut_key = FALLBACK_SHORTCUTS.get(marker.code, shortcut_key)

        marker.shortcut_key = shortcut_key
        marker.save(update_fields=['shortcut_key'])


class Migration(migrations.Migration):

    dependencies = [
        ('athletes', '0012_matchmarkertype_shortcut_key_and_seed_more_markers'),
    ]

    operations = [
        migrations.RunPython(normalize_marker_shortcuts, reverse_code=migrations.RunPython.noop),
    ]
