from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import StyledAuthenticationForm
from .views import (
    about_view,
    deactivate_account_view,
    home_view,
    match_game_action_create_view,
    match_game_action_delete_view,
    match_video_detail_view,
    match_video_statistics_view,
    match_video_upload_view,
    material_create_view,
    opponent_create_view,
    profile_edit_view,
    signup_view,
)

urlpatterns = [
    path('', home_view, name='home'),
    path('perfil/editar/', profile_edit_view, name='profile_edit'),
    path('perfil/desativar/', deactivate_account_view, name='deactivate_account'),
    path('partidas/video/upload/', match_video_upload_view, name='match_video_upload'),
    path('partidas/video/<int:video_id>/', match_video_detail_view, name='match_video_detail'),
    path('partidas/video/<int:video_id>/estatisticas/', match_video_statistics_view, name='match_video_statistics'),
    path('partidas/video/<int:video_id>/acoes/', match_game_action_create_view, name='match_game_action_create'),
    path('partidas/video/<int:video_id>/acoes/<int:action_id>/apagar/', match_game_action_delete_view, name='match_game_action_delete'),
    path('adversario/novo/', opponent_create_view, name='opponent_create'),
    path('material/novo/', material_create_view, name='material_create'),
    path('sobre/', about_view, name='about'),
    path('signup/', signup_view, name='signup'),
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='auth/login.html',
            authentication_form=StyledAuthenticationForm,
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
