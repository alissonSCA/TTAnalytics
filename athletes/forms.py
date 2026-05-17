from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction

from .models import AthleteProfile, Club, Competition, Grip, MatchVideo, Material, Opponent, Style


class StyledAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu usuario'}),
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Sua senha'}),
    )


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'voce@email.com'}),
    )
    photo = forms.ImageField(required=False, label='Foto')
    full_name = forms.CharField(
        max_length=120,
        label='Nome',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
    )
    birth_year = forms.IntegerField(
        min_value=1900,
        max_value=2100,
        label='Ano de nascimento',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2003', 'min': 1900, 'max': 2100, 'step': 1}),
    )
    grip = forms.ModelChoiceField(queryset=Grip.objects.none(), label='Empunhadura')
    dominant_hand = forms.ChoiceField(
        choices=AthleteProfile.DOMINANT_HAND_CHOICES,
        label='Mao dominante',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    style = forms.ModelChoiceField(queryset=Style.objects.none(), label='Estilo')
    material = forms.ModelChoiceField(queryset=Material.objects.none(), label='Material')
    club = forms.ModelChoiceField(queryset=Club.objects.none(), label='Clube')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escolha um usuario'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Senha'
        self.fields['password2'].label = 'Confirmar senha'
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Minimo de 8 caracteres'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Repita a senha'})

        self.fields['grip'].queryset = Grip.objects.all()
        self.fields['style'].queryset = Style.objects.all()
        self.fields['material'].queryset = Material.objects.all()
        self.fields['club'].queryset = Club.objects.all()

        select_class = {'class': 'form-control'}
        self.fields['grip'].widget.attrs.update(select_class)
        self.fields['style'].widget.attrs.update(select_class)
        self.fields['material'].widget.attrs.update(select_class)
        self.fields['club'].widget.attrs.update(select_class)
        self.fields['photo'].widget.attrs.update({'class': 'form-control'})

    def clean_birth_year(self):
        birth_year = self.cleaned_data['birth_year']
        if len(str(birth_year)) != 4:
            raise forms.ValidationError('O ano de nascimento deve ter exatamente 4 digitos.')
        return birth_year

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            AthleteProfile.objects.create(
                user=user,
                photo=self.cleaned_data.get('photo'),
                full_name=self.cleaned_data['full_name'],
                birth_year=self.cleaned_data['birth_year'],
                grip=self.cleaned_data['grip'],
                dominant_hand=self.cleaned_data['dominant_hand'],
                style=self.cleaned_data['style'],
                material=self.cleaned_data['material'],
                club=self.cleaned_data['club'],
            )
        return user


class AthleteProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = AthleteProfile
        fields = ('photo', 'full_name', 'birth_year', 'grip', 'dominant_hand', 'style', 'material', 'club')
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'birth_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2003'}),
            'dominant_hand': forms.Select(attrs={'class': 'form-control'}),
            'grip': forms.Select(attrs={'class': 'form-control'}),
            'style': forms.Select(attrs={'class': 'form-control'}),
            'material': forms.Select(attrs={'class': 'form-control'}),
            'club': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['photo'].label = 'Foto'
        self.fields['photo'].widget.attrs.update({'class': 'form-control'})


class MaterialCreateForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ('name', 'blade', 'forehand_rubber', 'backhand_rubber')
        labels = {
            'name': 'Nome do equipamento',
            'blade': 'Madeira',
            'forehand_rubber': 'Borracha forehand',
            'backhand_rubber': 'Borracha backhand',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Setup Grilo Ofensivo'}),
            'blade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Butterfly Timo Boll ALC'}),
            'forehand_rubber': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Dignics 09C'}),
            'backhand_rubber': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Tenergy 05 FX'}),
        }


class OpponentCreateForm(forms.ModelForm):
    class Meta:
        model = Opponent
        fields = ('name',)
        labels = {
            'name': 'Nome do adversario',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Joao Silva'}),
        }


class MatchVideoUploadForm(forms.ModelForm):
    athlete_one_profile = forms.ModelChoiceField(
        queryset=AthleteProfile.objects.none(),
        required=True,
        label='Atleta 1 (cadastro)',
        empty_label='Selecione o atleta',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    athlete_two_profile = forms.ModelChoiceField(
        queryset=AthleteProfile.objects.none(),
        required=False,
        label='Atleta 2 (cadastro)',
        empty_label='Selecione se o adversario estiver cadastrado',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    opponent = forms.ModelChoiceField(
        queryset=Opponent.objects.none(),
        required=False,
        label='Adversario (nao cadastrado como atleta)',
        empty_label='Selecione o adversario cadastrado',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    set_results_json = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = MatchVideo
        fields = (
            'video_file',
            'athlete_one_profile',
            'athlete_two_profile',
            'opponent',
            'competition',
            'match_date',
            'description',
        )
        labels = {
            'video_file': 'Video da partida',
            'competition': 'Competicao',
            'match_date': 'Data da partida',
            'description': 'Descricao do video',
        }
        widgets = {
            'video_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'competition': forms.Select(attrs={'class': 'form-control'}),
            'match_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descreva o contexto da partida'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['competition'].queryset = Competition.objects.all()
        self.fields['athlete_one_profile'].queryset = AthleteProfile.objects.all()
        self.fields['athlete_two_profile'].queryset = AthleteProfile.objects.all()
        self.fields['opponent'].queryset = Opponent.objects.all()

    def clean(self):
        cleaned_data = super().clean()

        athlete_one_profile = cleaned_data.get('athlete_one_profile')
        athlete_two_profile = cleaned_data.get('athlete_two_profile')
        opponent = cleaned_data.get('opponent')
        set_results_json = cleaned_data.get('set_results_json', '')

        if not athlete_one_profile:
            self.add_error('athlete_one_profile', 'Selecione o atleta 1 cadastrado.')

        if athlete_two_profile and opponent:
            self.add_error('opponent', 'Escolha apenas uma opcao: atleta 2 cadastrado ou adversario.')

        if not athlete_two_profile and not opponent:
            self.add_error('opponent', 'Selecione um adversario cadastrado ou um atleta 2 cadastrado.')

        # Validar dados de sets se fornecidos
        if set_results_json:
            import json
            try:
                set_results = json.loads(set_results_json)
                if not isinstance(set_results, list) or len(set_results) == 0:
                    self.add_error('set_results_json', 'Forneça pelo menos um set com os placares.')
                else:
                    for i, result in enumerate(set_results, 1):
                        if not isinstance(result, dict) or 'athlete_one' not in result or 'athlete_two' not in result:
                            self.add_error('set_results_json', f'Set {i} deve conter placares para ambos os atletas.')
                        else:
                            try:
                                a1 = int(result['athlete_one'])
                                a2 = int(result['athlete_two'])
                                if a1 < 0 or a2 < 0:
                                    self.add_error('set_results_json', f'Set {i}: os placares devem ser não-negativos.')
                            except (ValueError, TypeError):
                                self.add_error('set_results_json', f'Set {i}: os placares devem ser números inteiros.')
            except json.JSONDecodeError:
                self.add_error('set_results_json', 'Dados de sets inválidos.')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        athlete_one_profile = self.cleaned_data['athlete_one_profile']
        athlete_two_profile = self.cleaned_data.get('athlete_two_profile')
        opponent = self.cleaned_data.get('opponent')

        instance.athlete_one_name = athlete_one_profile.full_name
        if athlete_two_profile:
            instance.athlete_two_name = athlete_two_profile.full_name
        else:
            instance.athlete_two_name = opponent.name

        if commit:
            instance.save()
        return instance
