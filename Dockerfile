FROM python:3.14-slim-trixie@sha256:51dafde81dbdb6ebde285137a295cf18a47ca95234fe388a343719cb97305b3d AS base
RUN apt-get update \
    && apt-get upgrade --yes \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1

FROM base AS python-deps
WORKDIR /build
RUN pip install --no-cache-dir pipenv==2026.2.2
COPY Pipfile Pipfile.lock ./
RUN pipenv verify && pipenv requirements --hash > requirements.txt \
    && python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --require-hashes -r requirements.txt

FROM base AS runtime
ENV PATH="/opt/venv/bin:$PATH" PORT=5000
RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid 10001 --no-create-home appuser
WORKDIR /app
COPY --from=python-deps /opt/venv /opt/venv
COPY main.py gunicorn.conf.py ./
RUN /opt/venv/bin/python -m pip uninstall --yes pip \
    && /usr/local/bin/python -m pip uninstall --yes pip
USER 10001:10001
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '5000') + '/healthz', timeout=2)"
CMD ["gunicorn", "--config", "gunicorn.conf.py", "main:app"]
