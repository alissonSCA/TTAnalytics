# Table Tennis Analytics

Aplicação web para análise de partidas de tênis de mesa com marcação de ações no vídeo e dashboard de estatísticas.

## Requisitos

- Python 3.11+
- Ambiente virtual (`.venv`)

## Instalação

1. Entrar na pasta do projeto:

```bash
cd /home/alisson/Documents/src/TableTennisAnalytics
```

2. Criar e ativar o ambiente virtual (se necessário):

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Instalar dependências:

```bash
pip install -r requirements.txt
```

4. Aplicar migrações:

```bash
python manage.py migrate
```

## Executar

```bash
python manage.py runserver
```

Abra no navegador:

- `http://127.0.0.1:8000/`

## Comandos úteis

Checagem do projeto:

```bash
python manage.py check
```

Criar superusuário:

```bash
python manage.py createsuperuser
```

## Funcionalidades principais

- Upload e análise de vídeo de partidas
- Registro de ações com timeline
- Marcação de pontos e placar (sets/pontos)
- Dashboard de estatísticas da partida
- Heatmaps de distribuição das rebatidas