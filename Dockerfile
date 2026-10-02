FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

RUN groupadd --gid 10001 atmos \
    && useradd --uid 10001 --gid atmos --no-create-home --shell /usr/sbin/nologin atmos

COPY app/requirements.txt ./requirements.txt
RUN python -m pip install --requirement requirements.txt \
    && python -m pip uninstall --yes pip

COPY --chown=atmos:atmos app/app.py ./app.py
COPY --chown=atmos:atmos app/templates ./templates
COPY --chown=atmos:atmos app/static ./static

ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

USER 10001:10001

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=3).read()"]

CMD ["gunicorn", "--bind=0.0.0.0:8080", "--workers=2", "--threads=4", "--timeout=30", "--access-logfile=-", "--error-logfile=-", "app:app"]
