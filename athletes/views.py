from collections import Counter
import random

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.db.models import Q
import json

from .forms import AthleteProfileUpdateForm, MatchVideoUploadForm, MaterialCreateForm, OpponentCreateForm, SignUpForm
from .models import AthleteProfile, Competition, MatchGameAction, MatchMarkerType, MatchSetResult, MatchVideo


DUPLICATE_ACTION_WINDOW_SECONDS = 1.2
POINT_MARKER_CODES = ('point_my', 'point_opponent')
POINT_MARKER_LABEL_BY_CODE = {
	'point_my': 'Ponto Jogador 1',
	'point_opponent': 'Ponto Jogador 2',
}
TABLE_POSITION_KEY_TO_LABEL = {
	'7': 'Superior esquerda',
	'8': 'Superior centro',
	'9': 'Superior direita',
	'4': 'Meio esquerda',
	'5': 'Centro',
	'6': 'Meio direita',
	'1': 'Inferior esquerda',
	'2': 'Inferior centro',
	'3': 'Inferior direita',
}
TABLE_POSITION_LABEL_TO_KEY = {label.lower(): key for key, label in TABLE_POSITION_KEY_TO_LABEL.items()}
TABLE_POSITION_ROWS = (('7', '8', '9'), ('4', '5', '6'), ('1', '2', '3'))
TABLE_POSITION_CENTER_BY_KEY = {
	'7': {'x': 1 / 6, 'y': 1 / 6},
	'8': {'x': 3 / 6, 'y': 1 / 6},
	'9': {'x': 5 / 6, 'y': 1 / 6},
	'4': {'x': 1 / 6, 'y': 3 / 6},
	'5': {'x': 3 / 6, 'y': 3 / 6},
	'6': {'x': 5 / 6, 'y': 3 / 6},
	'1': {'x': 1 / 6, 'y': 5 / 6},
	'2': {'x': 3 / 6, 'y': 5 / 6},
	'3': {'x': 5 / 6, 'y': 5 / 6},
}
TABLE_POSITION_CELL_HALF_WIDTH = 1 / 6
TABLE_POSITION_CELL_HALF_HEIGHT = 1 / 6
TABLE_POSITION_GAUSSIAN_STD_DEV = 0.045


def _build_table_position_offset(key: str, index: int) -> tuple[float, float]:
	rng = random.Random(f'{key}:{index}')
	return rng.gauss(0, TABLE_POSITION_GAUSSIAN_STD_DEV), rng.gauss(0, TABLE_POSITION_GAUSSIAN_STD_DEV)


def _build_athlete_card(name: str, profile):
	photo_url = profile.photo.url if profile and profile.photo else None
	club_logo_url = None
	if profile and profile.club and profile.club.logo:
		club_logo_url = profile.club.logo.url
	return {
		'name': name,
		'photo_url': photo_url,
		'club_logo_url': club_logo_url,
		'initial': (name[:1] if name else 'A').upper(),
	}


def _get_table_position_key(position_label: str) -> str | None:
	if not position_label:
		return None
	return TABLE_POSITION_LABEL_TO_KEY.get(position_label.strip().lower())


def _empty_heatmap_counts() -> dict[str, int]:
	return {key: 0 for key in TABLE_POSITION_KEY_TO_LABEL}


def _build_heatmap_rows(counts: dict[str, int]) -> list[list[dict[str, float | int | str]]]:
	max_count = max(counts.values(), default=0)
	rows = []
	for row_keys in TABLE_POSITION_ROWS:
		row = []
		for key in row_keys:
			count = counts.get(key, 0)
			row.append(
				{
					'key': key,
					'label': TABLE_POSITION_KEY_TO_LABEL[key],
					'count': count,
					'intensity': (count / max_count) if max_count else 0,
				}
			)
		rows.append(row)
	return rows


def _build_heatmap_plot_payload(counts: dict[str, int]) -> dict:
	points = []
	for key, count in counts.items():
		center = TABLE_POSITION_CENTER_BY_KEY[key]
		for index in range(count):
			offset_x, offset_y = _build_table_position_offset(key, index)
			points.append(
				{
					'x': min(center['x'] + TABLE_POSITION_CELL_HALF_WIDTH * 0.95, max(center['x'] - TABLE_POSITION_CELL_HALF_WIDTH * 0.95, center['x'] + offset_x)),
					'y': min(center['y'] + TABLE_POSITION_CELL_HALF_HEIGHT * 0.95, max(center['y'] - TABLE_POSITION_CELL_HALF_HEIGHT * 0.95, center['y'] + offset_y)),
					'label': TABLE_POSITION_KEY_TO_LABEL[key],
					'cell_key': key,
				}
			)
	return {
		'points': points,
		'max_value': max(counts.values(), default=1),
		'z': [[counts.get(key, 0) for key in row_keys] for row_keys in TABLE_POSITION_ROWS],
		'labels': [[TABLE_POSITION_KEY_TO_LABEL[key] for key in row_keys] for row_keys in TABLE_POSITION_ROWS],
		'x': ['Esquerda', 'Centro', 'Direita'],
		'y': ['Fundo da mesa', 'Meia mesa', 'Curta'],
	}


def _build_match_statistics(video: MatchVideo) -> dict:
	actions = list(video.game_actions.select_related('marker_type').order_by('created_at'))
	rebatida_actions = [action for action in actions if action.action_type == 'first_to_fifth_ball']
	point_actions = [action for action in actions if action.action_type in POINT_MARKER_CODES]
	marker_counter = Counter()
	effect_counter = Counter()
	set_win_counter = Counter()
	set_results: list[dict[str, object]] = []
	rally_lengths: list[int] = []
	current_rally_positions: list[str] = []
	heatmap_counts = {
		'athlete_one_scored': _empty_heatmap_counts(),
		'athlete_one_conceded': _empty_heatmap_counts(),
		'athlete_two_scored': _empty_heatmap_counts(),
		'athlete_two_conceded': _empty_heatmap_counts(),
	}
	previous_set_athlete_one = 0
	previous_set_athlete_two = 0
	previous_action = None

	for action in actions:
		set_delta_athlete_one = action.set_athlete_one - previous_set_athlete_one
		set_delta_athlete_two = action.set_athlete_two - previous_set_athlete_two
		if set_delta_athlete_one > 0:
			set_win_counter['athlete_one'] += set_delta_athlete_one
			if previous_action is not None:
				for _ in range(set_delta_athlete_one):
					set_results.append({
						'set_number': len(set_results) + 1,
						'winner_key': 'athlete_one',
						'winner_name': video.athlete_one_name,
						'score_athlete_one': previous_action.point_athlete_one + 1,
						'score_athlete_two': previous_action.point_athlete_two,
					})
		if set_delta_athlete_two > 0:
			set_win_counter['athlete_two'] += set_delta_athlete_two
			if previous_action is not None:
				for _ in range(set_delta_athlete_two):
					set_results.append({
						'set_number': len(set_results) + 1,
						'winner_key': 'athlete_two',
						'winner_name': video.athlete_two_name,
						'score_athlete_one': previous_action.point_athlete_one,
						'score_athlete_two': previous_action.point_athlete_two + 1,
					})
		previous_set_athlete_one = action.set_athlete_one
		previous_set_athlete_two = action.set_athlete_two
		previous_action = action

		marker_label = POINT_MARKER_LABEL_BY_CODE.get(action.action_type, action.marker_type.name if action.marker_type else action.action_type)
		marker_counter[marker_label] += 1
		if action.action_type == 'first_to_fifth_ball':
			position_key = _get_table_position_key(action.detail_position)
			if position_key:
				current_rally_positions.append(position_key)
			if action.detail_effect:
				effect_counter[action.detail_effect] += 1
			continue

		if action.action_type not in POINT_MARKER_CODES:
			continue

		rally_lengths.append(len(current_rally_positions))
		if action.action_type == 'point_my':
			target_keys = ('athlete_one_scored', 'athlete_two_conceded')
		else:
			target_keys = ('athlete_two_scored', 'athlete_one_conceded')

		for position_key in current_rally_positions:
			for target_key in target_keys:
				heatmap_counts[target_key][position_key] += 1
		current_rally_positions = []

	total_points = len(point_actions)
	athlete_one_points = sum(1 for action in point_actions if action.action_type == 'point_my')
	athlete_two_points = total_points - athlete_one_points
	longest_rally = max(rally_lengths, default=0)
	average_rally_length = round(sum(rally_lengths) / len(rally_lengths), 1) if rally_lengths else 0
	last_action = actions[-1] if actions else None

	athletes = [
		{
			'key': 'athlete_one',
			'label': 'Jogador 1',
			'name': video.athlete_one_name,
			'photo_url': video.athlete_one_profile.photo.url if video.athlete_one_profile and video.athlete_one_profile.photo else None,
			'club_logo_url': video.athlete_one_profile.club.logo.url if video.athlete_one_profile and video.athlete_one_profile.club and video.athlete_one_profile.club.logo else None,
			'points_scored': athlete_one_points,
			'points_conceded': athlete_two_points,
			'sets_won': set_win_counter['athlete_one'],
			'point_share': round((athlete_one_points / total_points) * 100, 1) if total_points else 0,
			'scored_heatmap_rows': _build_heatmap_rows(heatmap_counts['athlete_one_scored']),
			'conceded_heatmap_rows': _build_heatmap_rows(heatmap_counts['athlete_one_conceded']),
			'scored_heatmap_plot': _build_heatmap_plot_payload(heatmap_counts['athlete_one_scored']),
			'conceded_heatmap_plot': _build_heatmap_plot_payload(heatmap_counts['athlete_one_conceded']),
		},
		{
			'key': 'athlete_two',
			'label': 'Jogador 2',
			'name': video.athlete_two_name,
			'photo_url': video.athlete_two_profile.photo.url if video.athlete_two_profile and video.athlete_two_profile.photo else None,
			'club_logo_url': video.athlete_two_profile.club.logo.url if video.athlete_two_profile and video.athlete_two_profile.club and video.athlete_two_profile.club.logo else None,
			'points_scored': athlete_two_points,
			'points_conceded': athlete_one_points,
			'sets_won': set_win_counter['athlete_two'],
			'point_share': round((athlete_two_points / total_points) * 100, 1) if total_points else 0,
			'scored_heatmap_rows': _build_heatmap_rows(heatmap_counts['athlete_two_scored']),
			'conceded_heatmap_rows': _build_heatmap_rows(heatmap_counts['athlete_two_conceded']),
			'scored_heatmap_plot': _build_heatmap_plot_payload(heatmap_counts['athlete_two_scored']),
			'conceded_heatmap_plot': _build_heatmap_plot_payload(heatmap_counts['athlete_two_conceded']),
		},
	]

	return {
		'athletes': athletes,
		'total_actions': len(actions),
		'total_rebatidas': len(rebatida_actions),
		'total_points': total_points,
		'total_sets': sum(set_win_counter.values()),
		'completed_rallies': len(rally_lengths),
		'average_rally_length': average_rally_length,
		'longest_rally': longest_rally,
		'sets_won_athlete_one': set_win_counter['athlete_one'],
		'sets_won_athlete_two': set_win_counter['athlete_two'],
		'set_results': set_results,
		'final_scoreboard': {
			'set_athlete_one': last_action.set_athlete_one if last_action else 0,
			'set_athlete_two': last_action.set_athlete_two if last_action else 0,
			'point_athlete_one': last_action.point_athlete_one if last_action else 0,
			'point_athlete_two': last_action.point_athlete_two if last_action else 0,
		},
		'marker_breakdown': marker_counter.most_common(),
		'effect_breakdown': effect_counter.most_common(),
	}


def _serialize_match_action(action: MatchGameAction) -> dict:
	display_label = POINT_MARKER_LABEL_BY_CODE.get(action.action_type, action.marker_type.name)
	return {
		'ok': True,
		'action_id': action.id,
		'action_type': action.action_type,
		'action_label': display_label,
		'marker_code': action.marker_type.code,
		'marker_name': display_label,
		'marker_color': action.marker_type.color,
		'marker_icon': action.marker_type.icon,
		'marker_shortcut': action.marker_type.shortcut_key,
		'detail_number': action.detail_number,
		'detail_effect': action.detail_effect,
		'detail_position': action.detail_position,
		'detail_summary': action.detail_summary,
		'time_signature': action.time_signature,
		'video_time_seconds': action.video_time_seconds,
		'set_athlete_one': action.set_athlete_one,
		'set_athlete_two': action.set_athlete_two,
		'point_athlete_one': action.point_athlete_one,
		'point_athlete_two': action.point_athlete_two,
	}


def _is_duplicate_match_action(existing_action: MatchGameAction, *, marker_type: MatchMarkerType, video_time_seconds: float, detail_number: int | None, detail_effect: str, detail_position: str, set_athlete_one: int, set_athlete_two: int, point_athlete_one: int, point_athlete_two: int) -> bool:
	if existing_action.marker_type_id != marker_type.id:
		return False
	if abs(existing_action.video_time_seconds - video_time_seconds) > DUPLICATE_ACTION_WINDOW_SECONDS:
		return False
	return (
		existing_action.detail_number == detail_number
		and existing_action.detail_effect == detail_effect
		and existing_action.detail_position == detail_position
		and existing_action.set_athlete_one == set_athlete_one
		and existing_action.set_athlete_two == set_athlete_two
		and existing_action.point_athlete_one == point_athlete_one
		and existing_action.point_athlete_two == point_athlete_two
	)


def _resolve_return_url(source: str, material_id: int | None = None, opponent_id: int | None = None) -> str:
	allowed_sources = {
		'signup': 'signup',
		'profile_edit': 'profile_edit',
		'match_video_upload': 'match_video_upload',
	}
	url_name = allowed_sources.get(source, 'signup')
	base = reverse(url_name)
	params = []
	if material_id is not None:
		params.append(f'material_id={material_id}')
	if opponent_id is not None:
		params.append(f'opponent_id={opponent_id}')
	if not params:
		return base
	separator = '&' if '?' in base else '?'
	return f"{base}{separator}{'&'.join(params)}"


def signup_view(request: HttpRequest):
	if request.user.is_authenticated:
		return redirect('home')

	selected_material_id = request.GET.get('material_id')

	if request.method == 'POST':
		form = SignUpForm(request.POST, request.FILES)
		if form.is_valid():
			user = form.save()
			login(request, user)
			return redirect('home')
	else:
		initial = {}
		if selected_material_id and selected_material_id.isdigit():
			initial['material'] = int(selected_material_id)
		form = SignUpForm(initial=initial)

	return render(request, 'auth/signup.html', {'form': form})


@login_required
def home_view(request):
	profile = getattr(request.user, 'athlete_profile', None)
	selected_competition = request.GET.get('home_competition', '').strip()
	selected_athlete = request.GET.get('home_athlete', '').strip()
	selected_order = request.GET.get('home_order', 'recent').strip()

	highlight_matches = MatchVideo.objects.filter(uploaded_by=request.user).select_related('competition')

	if selected_competition.isdigit():
		highlight_matches = highlight_matches.filter(competition_id=int(selected_competition))

	if selected_athlete:
		highlight_matches = highlight_matches.filter(
			Q(athlete_one_name__icontains=selected_athlete)
			| Q(athlete_two_name__icontains=selected_athlete)
			| Q(opponent__name__icontains=selected_athlete)
		)

	if selected_order == 'oldest':
		highlight_matches = highlight_matches.order_by('match_date', 'created_at')
	else:
		highlight_matches = highlight_matches.order_by('-match_date', '-created_at')

	highlight_matches = highlight_matches[:8]
	home_competitions = Competition.objects.all()
	return render(
		request,
		'athletes/home.html',
		{
			'profile': profile,
			'highlight_matches': highlight_matches,
			'home_competitions': home_competitions,
			'selected_home_competition': selected_competition,
			'selected_home_athlete': selected_athlete,
			'selected_home_order': selected_order,
		},
	)


@login_required
def profile_edit_view(request):
	profile = getattr(request.user, 'athlete_profile', None)
	if profile is None:
		messages.error(request, 'Perfil de atleta nao encontrado para este usuario.')
		return redirect('home')

	selected_material_id = request.GET.get('material_id')

	if request.method == 'POST':
		form = AthleteProfileUpdateForm(request.POST, request.FILES, instance=profile)
		if form.is_valid():
			form.save()
			messages.success(request, 'Perfil atualizado com sucesso.')
			return redirect('home')
	else:
		initial = {}
		if selected_material_id and selected_material_id.isdigit():
			initial['material'] = int(selected_material_id)
		form = AthleteProfileUpdateForm(instance=profile, initial=initial)

	return render(request, 'athletes/profile_edit.html', {'form': form, 'profile': profile})


@login_required
def deactivate_account_view(request):
	if request.method != 'POST':
		return redirect('home')

	user = request.user
	user.is_active = False
	user.save(update_fields=['is_active'])
	logout(request)
	messages.success(request, 'Conta desativada. Para reativar, contate o administrador.')
	return redirect('login')


def about_view(request):
	return render(request, 'about.html')


def material_create_view(request: HttpRequest):
	source = request.GET.get('source', 'signup')

	if request.method == 'POST':
		form = MaterialCreateForm(request.POST)
		source = request.POST.get('source', source)
		if form.is_valid():
			material = form.save()
			messages.success(request, 'Equipamento cadastrado com sucesso. Selecione-o no formulario.')
			return redirect(_resolve_return_url(source, material.id))
	else:
		form = MaterialCreateForm()

	context = {
		'form': form,
		'source': source,
		'return_url': _resolve_return_url(source),
	}
	return render(request, 'athletes/material_create.html', context)


@login_required
def opponent_create_view(request: HttpRequest):
	source = request.GET.get('source', 'match_video_upload')

	if request.method == 'POST':
		form = OpponentCreateForm(request.POST)
		source = request.POST.get('source', source)
		if form.is_valid():
			opponent = form.save()
			messages.success(request, 'Adversario cadastrado com sucesso. Selecione-o no formulario.')
			return redirect(_resolve_return_url(source, opponent_id=opponent.id))
	else:
		form = OpponentCreateForm()

	context = {
		'form': form,
		'source': source,
		'return_url': _resolve_return_url(source),
	}
	return render(request, 'athletes/opponent_create.html', context)


@login_required
def match_video_upload_view(request: HttpRequest):
	if request.method == 'POST':
		form = MatchVideoUploadForm(request.POST, request.FILES)
		if form.is_valid():
			video = form.save(commit=False)
			video.uploaded_by = request.user
			video.save()
			
			# Processar dados de sets se fornecidos
			set_results_json = form.cleaned_data.get('set_results_json', '')
			if set_results_json:
				try:
					set_results = json.loads(set_results_json)
					for i, result in enumerate(set_results, 1):
						MatchSetResult.objects.create(
							match_video=video,
							set_number=i,
							athlete_one_score=int(result['athlete_one']),
							athlete_two_score=int(result['athlete_two']),
						)
				except (json.JSONDecodeError, ValueError, TypeError) as e:
					messages.error(request, f'Erro ao salvar dados de sets: {str(e)}')
					return redirect('match_video_upload')
			
			messages.success(request, 'Video enviado com sucesso.')
			return redirect('match_video_upload')
	else:
		form = MatchVideoUploadForm()

	selected_competition = request.GET.get('competition', '').strip()
	selected_athlete = request.GET.get('athlete', '').strip()

	videos = MatchVideo.objects.select_related('competition', 'athlete_one_profile', 'athlete_two_profile').order_by('-created_at')

	if selected_competition.isdigit():
		videos = videos.filter(competition_id=int(selected_competition))

	videos = videos[:30]
	competitions = Competition.objects.all()
	athletes = AthleteProfile.objects.all()

	context = {
		'form': form,
		'recent_videos': videos,
		'competitions': competitions,
		'athletes': athletes,
		'selected_competition': selected_competition,
		'selected_athlete': selected_athlete,
	}
	return render(request, 'athletes/video_upload.html', context)


@login_required
def match_video_detail_view(request: HttpRequest, video_id: int):
	video = get_object_or_404(
		MatchVideo.objects.select_related('competition', 'athlete_one_profile', 'athlete_two_profile'),
		id=video_id,
		uploaded_by=request.user,
	)
	last_action = video.game_actions.order_by('-created_at').first()
	match_actions = video.game_actions.select_related('created_by', 'marker_type').order_by('-created_at')
	marker_types = MatchMarkerType.objects.filter(is_active=True).order_by('sort_order', 'name')
	default_marker = marker_types.filter(code='start_game').first() or marker_types.first()
	initial_scoreboard = {
		'set_athlete_one': last_action.set_athlete_one if last_action else 0,
		'set_athlete_two': last_action.set_athlete_two if last_action else 0,
		'point_athlete_one': last_action.point_athlete_one if last_action else 0,
		'point_athlete_two': last_action.point_athlete_two if last_action else 0,
	}

	athlete_one_card = _build_athlete_card(video.athlete_one_name, video.athlete_one_profile)
	athlete_two_card = _build_athlete_card(video.athlete_two_name, video.athlete_two_profile)

	return render(
		request,
		'athletes/match_video_detail.html',
		{
			'video': video,
			'athlete_one_card': athlete_one_card,
			'athlete_two_card': athlete_two_card,
			'initial_scoreboard': initial_scoreboard,
			'match_actions': match_actions,
			'marker_types': marker_types,
			'default_marker': default_marker,
		},
	)


@login_required
def match_video_statistics_view(request: HttpRequest, video_id: int):
	video = get_object_or_404(
		MatchVideo.objects.select_related('competition', 'athlete_one_profile', 'athlete_two_profile'),
		id=video_id,
		uploaded_by=request.user,
	)
	statistics = _build_match_statistics(video)
	return render(
		request,
		'athletes/match_video_statistics.html',
		{
			'video': video,
			'athlete_one_card': _build_athlete_card(video.athlete_one_name, video.athlete_one_profile),
			'athlete_two_card': _build_athlete_card(video.athlete_two_name, video.athlete_two_profile),
			'statistics': statistics,
		},
	)


@login_required
def match_game_action_create_view(request: HttpRequest, video_id: int):
	if request.method != 'POST':
		return JsonResponse({'ok': False, 'error': 'Metodo nao permitido.'}, status=405)

	video = get_object_or_404(MatchVideo, id=video_id, uploaded_by=request.user)

	try:
		payload = json.loads(request.body.decode('utf-8'))
	except json.JSONDecodeError:
		return JsonResponse({'ok': False, 'error': 'JSON invalido.'}, status=400)

	action_type = payload.get('action_type')
	marker_type_id = payload.get('marker_type_id')
	marker_type = None
	if marker_type_id:
		try:
			marker_type = MatchMarkerType.objects.get(id=int(marker_type_id), is_active=True)
		except (MatchMarkerType.DoesNotExist, TypeError, ValueError):
			return JsonResponse({'ok': False, 'error': 'Marcador invalido.'}, status=400)
	if marker_type is None:
		return JsonResponse({'ok': False, 'error': 'Selecione um marcador valido.'}, status=400)

	try:
		video_time_seconds = float(payload.get('video_time_seconds', 0))
	except (TypeError, ValueError):
		return JsonResponse({'ok': False, 'error': 'Tempo de video invalido.'}, status=400)

	if video_time_seconds < 0:
		video_time_seconds = 0

	def parse_non_negative_int(value, field_name):
		try:
			parsed = int(value)
		except (TypeError, ValueError):
			raise ValueError(f'Campo {field_name} invalido.')
		if parsed < 0:
			raise ValueError(f'Campo {field_name} nao pode ser negativo.')
		return parsed

	try:
		set_athlete_one = parse_non_negative_int(payload.get('set_athlete_one', 0), 'set_athlete_one')
		set_athlete_two = parse_non_negative_int(payload.get('set_athlete_two', 0), 'set_athlete_two')
		point_athlete_one = parse_non_negative_int(payload.get('point_athlete_one', 0), 'point_athlete_one')
		point_athlete_two = parse_non_negative_int(payload.get('point_athlete_two', 0), 'point_athlete_two')
		if marker_type.code == 'first_to_fifth_ball':
			detail_number = payload.get('detail_number')
			detail_number = parse_non_negative_int(detail_number, 'detail_number') if detail_number not in (None, '') else None
			if detail_number is None or detail_number < 1:
				raise ValueError('Campo detail_number deve iniciar em 1.')
			detail_effect = str(payload.get('detail_effect', '')).strip()
			detail_position = str(payload.get('detail_position', '')).strip()
		else:
			detail_number = None
			detail_effect = ''
			detail_position = ''
	except ValueError as exc:
		return JsonResponse({'ok': False, 'error': str(exc)}, status=400)

	time_signature = payload.get('time_signature', '').strip()
	if not time_signature:
		time_signature = '00:00.000'

	recent_similar_action = video.game_actions.filter(marker_type=marker_type).order_by('-created_at').first()
	if recent_similar_action and _is_duplicate_match_action(
		recent_similar_action,
		marker_type=marker_type,
		video_time_seconds=video_time_seconds,
		detail_number=detail_number,
		detail_effect=detail_effect,
		detail_position=detail_position,
		set_athlete_one=set_athlete_one,
		set_athlete_two=set_athlete_two,
		point_athlete_one=point_athlete_one,
		point_athlete_two=point_athlete_two,
	):
		return JsonResponse(
			{
				'ok': False,
				'error': 'Marcacao duplicada em intervalo muito curto.',
				'duplicate_action_id': recent_similar_action.id,
			},
			status=409,
		)

	action = MatchGameAction.objects.create(
		match_video=video,
		created_by=request.user,
		marker_type=marker_type,
		action_type=marker_type.code,
		detail_number=detail_number,
		detail_effect=detail_effect,
		detail_position=detail_position,
		video_time_seconds=video_time_seconds,
		time_signature=time_signature,
		set_athlete_one=set_athlete_one,
		set_athlete_two=set_athlete_two,
		point_athlete_one=point_athlete_one,
		point_athlete_two=point_athlete_two,
	)

	return JsonResponse(_serialize_match_action(action))


@login_required
def match_game_action_delete_view(request: HttpRequest, video_id: int, action_id: int):
	if request.method != 'POST':
		return JsonResponse({'ok': False, 'error': 'Metodo nao permitido.'}, status=405)

	action = get_object_or_404(
		MatchGameAction.objects.select_related('match_video'),
		id=action_id,
		match_video_id=video_id,
		match_video__uploaded_by=request.user,
	)
	action.delete()
	return JsonResponse({'ok': True, 'action_id': action_id})
