from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone


class Grip(models.Model):
	name = models.CharField(max_length=60, unique=True)

	class Meta:
		ordering = ['name']
		verbose_name = 'Empunhadura'
		verbose_name_plural = 'Empunhaduras'

	def __str__(self) -> str:
		return self.name


class Style(models.Model):
	name = models.CharField(max_length=60, unique=True)

	class Meta:
		ordering = ['name']
		verbose_name = 'Estilo'
		verbose_name_plural = 'Estilos'

	def __str__(self) -> str:
		return self.name


class Material(models.Model):
	name = models.CharField(max_length=80, unique=True)
	blade = models.CharField(max_length=80)
	forehand_rubber = models.CharField(max_length=80)
	backhand_rubber = models.CharField(max_length=80)

	class Meta:
		ordering = ['name']
		verbose_name = 'Material'
		verbose_name_plural = 'Materiais'

	def __str__(self) -> str:
		return self.name


class Club(models.Model):
	name = models.CharField(max_length=90, unique=True)
	short_name = models.CharField('Nome curto', max_length=40, blank=True)
	logo = models.ImageField(upload_to='clubs/logos/', blank=True, null=True)

	class Meta:
		ordering = ['name']
		verbose_name = 'Clube'
		verbose_name_plural = 'Clubes'

	def __str__(self) -> str:
		if self.short_name:
			return f'{self.short_name} - {self.name}'
		return self.name


class Competition(models.Model):
	name = models.CharField('Competicao', max_length=120, unique=True)

	class Meta:
		ordering = ['name']
		verbose_name = 'Competicao'
		verbose_name_plural = 'Competicoes'

	def __str__(self) -> str:
		return self.name


class Opponent(models.Model):
	name = models.CharField('Nome do adversario', max_length=120, unique=True)

	class Meta:
		ordering = ['name']
		verbose_name = 'Adversario'
		verbose_name_plural = 'Adversarios'

	def __str__(self) -> str:
		return self.name


class AthleteProfile(models.Model):
	RIGHT = 'R'
	LEFT = 'L'
	DOMINANT_HAND_CHOICES = [
		(RIGHT, 'Destro'),
		(LEFT, 'Canhoto'),
	]

	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='athlete_profile')
	photo = models.ImageField(upload_to='athletes/photos/', blank=True, null=True)
	full_name = models.CharField('Nome', max_length=120)
	birth_year = models.PositiveSmallIntegerField(
		'Ano de nascimento',
		validators=[MinValueValidator(1900), MaxValueValidator(2100)],
	)
	grip = models.ForeignKey(Grip, on_delete=models.PROTECT, verbose_name='Empunhadura')
	dominant_hand = models.CharField(
		'Mao dominante',
		max_length=1,
		choices=DOMINANT_HAND_CHOICES,
	)
	style = models.ForeignKey(Style, on_delete=models.PROTECT, verbose_name='Estilo')
	material = models.ForeignKey(Material, on_delete=models.PROTECT, verbose_name='Material')
	club = models.ForeignKey(Club, on_delete=models.PROTECT, verbose_name='Clube')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['full_name']
		verbose_name = 'Perfil de atleta'
		verbose_name_plural = 'Perfis de atletas'

	def __str__(self) -> str:
		return self.full_name

	@property
	def calculated_age(self) -> int:
		# Considerando nascimento em 1o de janeiro.
		return timezone.now().year - self.birth_year


class MatchVideo(models.Model):
	uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_match_videos')
	athlete_one_profile = models.ForeignKey(
		AthleteProfile,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='match_videos_as_athlete_one',
		verbose_name='Atleta 1 (cadastro)',
	)
	athlete_two_profile = models.ForeignKey(
		AthleteProfile,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='match_videos_as_athlete_two',
		verbose_name='Atleta 2 (cadastro)',
	)
	athlete_one_name = models.CharField('Atleta 1', max_length=120)
	athlete_two_name = models.CharField('Atleta 2', max_length=120)
	competition = models.ForeignKey(Competition, on_delete=models.PROTECT, verbose_name='Competicao')
	match_date = models.DateField('Data da partida')
	description = models.TextField('Descricao do video', blank=True)
	video_file = models.FileField('Video', upload_to='matches/videos/%Y/%m/%d/')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		verbose_name = 'Video de partida'
		verbose_name_plural = 'Videos de partidas'

	def __str__(self) -> str:
		return f'{self.athlete_one_name} vs {self.athlete_two_name} - {self.competition.name}'


class MatchSetResult(models.Model):
	match_video = models.ForeignKey(MatchVideo, on_delete=models.CASCADE, related_name='set_results')
	set_number = models.PositiveSmallIntegerField('Número do set')
	athlete_one_score = models.PositiveSmallIntegerField('Pontuação atleta 1')
	athlete_two_score = models.PositiveSmallIntegerField('Pontuação atleta 2')

	class Meta:
		ordering = ['set_number']
		verbose_name = 'Resultado de set'
		verbose_name_plural = 'Resultados de sets'
		unique_together = ('match_video', 'set_number')

	def __str__(self) -> str:
		return f'Set {self.set_number}: {self.athlete_one_score} x {self.athlete_two_score}'


class MatchMarkerType(models.Model):
	code = models.CharField(max_length=40, unique=True)
	name = models.CharField(max_length=80, unique=True)
	color = models.CharField(max_length=20)
	icon = models.CharField(max_length=12)
	shortcut_key = models.CharField(
		max_length=1,
		unique=True,
		blank=True,
		null=True,
		validators=[RegexValidator(r'^[A-Za-z]$', 'Use apenas uma letra para o atalho.')],
	)
	sort_order = models.PositiveSmallIntegerField(default=0)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ['sort_order', 'name']
		verbose_name = 'Tipo de marcador'
		verbose_name_plural = 'Tipos de marcadores'

	def __str__(self) -> str:
		return self.name

	def clean(self):
		super().clean()
		if self.shortcut_key:
			self.shortcut_key = self.shortcut_key.upper()


class MatchGameAction(models.Model):
	match_video = models.ForeignKey(MatchVideo, on_delete=models.CASCADE, related_name='game_actions')
	created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='match_game_actions')
	marker_type = models.ForeignKey(MatchMarkerType, on_delete=models.PROTECT, related_name='game_actions', null=True, blank=True)
	action_type = models.CharField(max_length=40)
	detail_number = models.PositiveSmallIntegerField(blank=True, null=True)
	detail_effect = models.CharField(max_length=40, blank=True)
	detail_position = models.CharField(max_length=80, blank=True)
	video_time_seconds = models.FloatField(default=0)
	time_signature = models.CharField(max_length=20)
	set_athlete_one = models.PositiveSmallIntegerField(default=0)
	set_athlete_two = models.PositiveSmallIntegerField(default=0)
	point_athlete_one = models.PositiveSmallIntegerField(default=0)
	point_athlete_two = models.PositiveSmallIntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['created_at']
		verbose_name = 'Acao de jogo'
		verbose_name_plural = 'Acoes de jogo'

	def __str__(self) -> str:
		marker_name = self.marker_type.name if self.marker_type else self.action_type
		return f'{marker_name} @ {self.time_signature}'

	@property
	def detail_summary(self) -> str:
		details = []
		if self.detail_number is not None:
			details.append(f'#{self.detail_number}')
		if self.detail_effect:
			details.append(self.detail_effect)
		if self.detail_position:
			details.append(self.detail_position)
		return ' | '.join(details)
