# Table Tennis Analytics

Aplicação web para análise de partidas de tênis de mesa com marcação de ações no vídeo e dashboard de estatísticas.

## Requisitos

- Python 3.11+
- Ambiente virtual (`.venv`)

## Deploy com Docker

O projeto agora inclui `Dockerfile`, `docker-compose.yml`, nginx e workflow de GitHub Actions para deploy via SSH.

1. Copie `.env.example` para `.env` e ajuste os valores de produção.
2. No servidor, deixe o repositório clonado em um diretório fixo, com Docker e Docker Compose instalados.
3. Configure os secrets do GitHub Actions:
	- `SSH_HOST`
	- `SSH_USER`
	- `SSH_KEY`
	- `SSH_PORT` opcional
	- `DEPLOY_PATH`
4. Faça push para `main` para disparar o deploy.

Na primeira vez, clone o repositório manualmente no caminho indicado por `DEPLOY_PATH` e crie o arquivo `.env` nesse diretório.

O nginx expõe a aplicação na porta 8001 no servidor, e os arquivos de `static/` e `media/` ficam em volumes compartilhados.

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