from django.db import migrations, models


MARKER_ROWS = [
    {'code': 'start_game', 'name': 'Inicio de jogo', 'color': '#126e52', 'icon': '▶', 'shortcut_key': 'J', 'sort_order': 1},
    {'code': 'first_to_fifth_ball', 'name': '1ª a 5ª bola', 'color': '#2f6fdb', 'icon': '⑤', 'shortcut_key': 'B', 'sort_order': 2},
    {'code': 'point_my', 'name': 'Ponto meu', 'color': '#e5a100', 'icon': '↑', 'shortcut_key': 'M', 'sort_order': 3},
    {'code': 'point_opponent', 'name': 'Ponto do adversario', 'color': '#b42318', 'icon': '↓', 'shortcut_key': 'A', 'sort_order': 4},
    {'code': 'technical_timeout', 'name': 'Tempo tecnico', 'color': '#7a4dbf', 'icon': '⏱', 'shortcut_key': 'T', 'sort_order': 5},
    {'code': 'pause_restart', 'name': 'Pausa / reinicio', 'color': '#64748b', 'icon': '⏸', 'shortcut_key': 'R', 'sort_order': 6},
    {'code': 'start_set', 'name': 'Inicio de set', 'color': '#0f766e', 'icon': '1', 'shortcut_key': 'I', 'sort_order': 7},
    {'code': 'end_set', 'name': 'Fim de set', 'color': '#f97316', 'icon': '2', 'shortcut_key': 'F', 'sort_order': 8},
    {'code': 'end_game', 'name': 'Fim de jogo', 'color': '#111827', 'icon': '🏁', 'shortcut_key': 'G', 'sort_order': 9},
]


def seed_marker_types(apps, schema_editor):
    MatchMarkerType = apps.get_model('athletes', 'MatchMarkerType')
    for row in MARKER_ROWS:
        MatchMarkerType.objects.update_or_create(code=row['code'], defaults=row)


def backfill_marker_types(apps, schema_editor):
    MatchMarkerType = apps.get_model('athletes', 'MatchMarkerType')
    MatchGameAction = apps.get_model('athletes', 'MatchGameAction')

    marker_map = {marker.code: marker for marker in MatchMarkerType.objects.all()}
    default_marker = marker_map.get('start_game') or next(iter(marker_map.values()), None)

    for action in MatchGameAction.objects.select_related('match_video').all():
        marker_type = marker_map.get(action.action_type) or default_marker
        if marker_type is not None:
            action.marker_type_id = marker_type.id
            action.action_type = marker_type.code
            action.save(update_fields=['marker_type', 'action_type'])


class Migration(migrations.Migration):

    dependencies = [
        ('athletes', '0011_matchmarkertype_alter_matchgameaction_action_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='matchmarkertype',
            name='shortcut_key',
            field=models.CharField(blank=True, max_length=1, null=True, unique=True),
        ),
        migrations.RunPython(seed_marker_types, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(backfill_marker_types, reverse_code=migrations.RunPython.noop),
    ]
