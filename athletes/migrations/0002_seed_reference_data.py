from django.db import migrations


def seed_reference_data(apps, schema_editor):
    Grip = apps.get_model('athletes', 'Grip')
    Style = apps.get_model('athletes', 'Style')
    Material = apps.get_model('athletes', 'Material')
    Club = apps.get_model('athletes', 'Club')

    for name in ['Classica Shakehand', 'Caneta Japonesa', 'Caneta Chinesa']:
        Grip.objects.get_or_create(name=name)

    for name in ['Ofensivo', 'Allround', 'Defensivo Moderno', 'Bloqueador']:
        Style.objects.get_or_create(name=name)

    materials = [
        {
            'name': 'Setup Veloz Carbon',
            'blade': 'Butterfly Timo Boll ALC',
            'forehand_rubber': 'Dignics 09C',
            'backhand_rubber': 'Tenergy 05 FX',
        },
        {
            'name': 'Setup Controle Classico',
            'blade': 'Stiga Allround Classic',
            'forehand_rubber': 'Yasaka Rakza 7',
            'backhand_rubber': 'Xiom Vega Europe',
        },
        {
            'name': 'Setup Ataque Caneta',
            'blade': 'DHS Hurricane Long 5',
            'forehand_rubber': 'Hurricane 3 Neo',
            'backhand_rubber': 'Butterfly Rozena',
        },
    ]

    for material in materials:
        Material.objects.get_or_create(name=material['name'], defaults=material)

    for name in ['Clube Spin Rio', 'Academia Loop Forte', 'Centro TT Sao Paulo', 'Mesa Rapida Campinas']:
        Club.objects.get_or_create(name=name)


def unseed_reference_data(apps, schema_editor):
    Grip = apps.get_model('athletes', 'Grip')
    Style = apps.get_model('athletes', 'Style')
    Material = apps.get_model('athletes', 'Material')
    Club = apps.get_model('athletes', 'Club')

    Grip.objects.filter(name__in=['Classica Shakehand', 'Caneta Japonesa', 'Caneta Chinesa']).delete()
    Style.objects.filter(name__in=['Ofensivo', 'Allround', 'Defensivo Moderno', 'Bloqueador']).delete()
    Material.objects.filter(name__in=['Setup Veloz Carbon', 'Setup Controle Classico', 'Setup Ataque Caneta']).delete()
    Club.objects.filter(name__in=['Clube Spin Rio', 'Academia Loop Forte', 'Centro TT Sao Paulo', 'Mesa Rapida Campinas']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('athletes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_reference_data, reverse_code=unseed_reference_data),
    ]
