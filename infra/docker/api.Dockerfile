# syntax=docker/dockerfile:1.7
FROM python:3.12.7-slim-bookworm AS base
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

FROM base AS builder
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY apps/api/requirements.txt apps/api/requirements-dev.txt ./
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

FROM builder AS builder-dev
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements-dev.txt watchdog[watchmedo]

FROM base AS runtime
ENV PATH="/opt/venv/bin:$PATH" DJANGO_SETTINGS_MODULE=patchbeast.settings.prod
RUN useradd --system --uid 10001 --create-home app && mkdir -p /app/staticfiles && chown -R app /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=app apps/api/ /app/
COPY --chown=app infra/docker/api-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
 && DJANGO_SECRET_KEY=build DATABASE_URL=sqlite:////tmp/x REDIS_URL=redis://x python manage.py collectstatic --noinput
USER app
EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "patchbeast.wsgi:application", "-b", "0.0.0.0:8000"]

FROM base AS dev
ENV PATH="/opt/venv/bin:$PATH"
COPY --from=builder-dev /opt/venv /opt/venv
RUN mkdir -p /repo/packages/api-client
COPY infra/docker/api-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
