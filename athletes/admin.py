from django.contrib import admin
from django.utils.html import format_html

from .models import AthleteProfile, Club, Competition, Grip, MatchGameAction, MatchMarkerType, MatchSetResult, MatchVideo, Material, Opponent, Style


@admin.register(Grip)
class GripAdmin(admin.ModelAdmin):
	list_display = ('name',)
	search_fields = ('name',)


@admin.register(Style)
class StyleAdmin(admin.ModelAdmin):
	list_display = ('name',)
	search_fields = ('name',)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
	list_display = ('name', 'blade', 'forehand_rubber', 'backhand_rubber')
	search_fields = ('name', 'blade', 'forehand_rubber', 'backhand_rubber')


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
	list_display = ('name', 'short_name', 'logo_preview')
	search_fields = ('name', 'short_name')
	readonly_fields = ('logo_preview',)

	def logo_preview(self, obj):
		if obj.logo:
			return format_html('<img src="{}" style="height: 44px; border-radius: 6px;" />', obj.logo.url)
		return 'Sem logo'

	logo_preview.short_description = 'Preview da logo'


@admin.register(AthleteProfile)
class AthleteProfileAdmin(admin.ModelAdmin):
	list_display = ('full_name', 'birth_year', 'dominant_hand', 'club', 'style')
	list_filter = ('dominant_hand', 'club', 'style', 'grip')
	search_fields = ('full_name', 'user__username', 'club__name')


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
	list_display = ('name',)
	search_fields = ('name',)


@admin.register(Opponent)
class OpponentAdmin(admin.ModelAdmin):
	list_display = ('name',)
	search_fields = ('name',)


@admin.register(MatchVideo)
class MatchVideoAdmin(admin.ModelAdmin):
	list_display = (
		'uploaded_by',
		'athlete_one_name',
		'athlete_one_profile',
		'athlete_two_name',
		'athlete_two_profile',
		'opponent',
		'competition',
		'match_date',
		'description',
		'created_at',
	)
	list_filter = ('competition', 'match_date', 'created_at')
	search_fields = ('uploaded_by__username', 'athlete_one_name', 'athlete_two_name', 'competition__name')


@admin.register(MatchSetResult)
class MatchSetResultAdmin(admin.ModelAdmin):
	list_display = ('match_video', 'set_number', 'athlete_one_score', 'athlete_two_score')
	list_filter = ('set_number', 'match_video__competition')
	search_fields = ('match_video__athlete_one_name', 'match_video__athlete_two_name')
	readonly_fields = ('match_video', 'set_number')


@admin.register(MatchMarkerType)
class MatchMarkerTypeAdmin(admin.ModelAdmin):
	list_display = ('name', 'code', 'shortcut_key', 'color_preview', 'icon', 'sort_order', 'is_active')
	list_editable = ('shortcut_key', 'sort_order', 'is_active')
	search_fields = ('name', 'code', 'shortcut_key', 'icon', 'color')
	list_filter = ('is_active',)

	def color_preview(self, obj):
		return format_html(
			'<span style="display:inline-flex;align-items:center;gap:0.4rem;">'
			'<span style="width:18px;height:18px;border-radius:50%;background:{};display:inline-block;border:1px solid rgba(0,0,0,0.15);"></span>'
			'<span>{}</span></span>',
			obj.color,
			obj.icon,
		)

	color_preview.short_description = 'Cor / ícone'


@admin.register(MatchGameAction)
class MatchGameActionAdmin(admin.ModelAdmin):
	list_display = (
		'match_video',
		'action_type',
		'detail_number',
		'detail_effect',
		'detail_position',
		'time_signature',
		'set_athlete_one',
		'set_athlete_two',
		'point_athlete_one',
		'point_athlete_two',
		'created_by',
		'created_at',
	)
	list_filter = ('action_type', 'created_at')
	search_fields = ('match_video__athlete_one_name', 'match_video__athlete_two_name', 'created_by__username')
