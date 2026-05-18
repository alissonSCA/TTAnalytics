FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
	&& apt-get install -y --no-install-recommends build-essential libjpeg62-turbo zlib1g \
	&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

RUN pip install --upgrade pip \
	&& pip install -r requirements.txt

COPY . /app/

RUN mkdir -p /vol/web/static /vol/web/media /vol/web/db \
	&& useradd --create-home --shell /bin/bash appuser \
	&& chown -R appuser:appuser /app /vol/web

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER appuser

ENTRYPOINT ["/entrypoint.sh"]