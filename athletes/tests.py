from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Competition, MatchVideo


class MatchVideoDetailKeyboardShortcutsTests(TestCase):
    def test_detail_page_ignores_enter_hotkey_on_detail_buttons(self):
        user = User.objects.create_user(username='tester', password='test123')
        competition = Competition.objects.create(name='Copa Teste')
        video = MatchVideo.objects.create(
            uploaded_by=user,
            athlete_one_name='Jogador 1',
            athlete_two_name='Jogador 2',
            competition=competition,
            match_date='2026-01-01',
            video_file=SimpleUploadedFile('match.mp4', b'fake-video-content', content_type='video/mp4'),
        )

        self.client.force_login(user)
        response = self.client.get(reverse('match_video_detail', args=[video.id]))

        self.assertContains(
            response,
            "const isButtonContext = target && target.tagName === 'BUTTON';",
        )
        self.assertContains(
            response,
            'Enter:</strong> salvar o marcador selecionado (fora dos botoes de detalhe)',
        )
