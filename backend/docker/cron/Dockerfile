FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install --no-cache-dir .

COPY docker/cron/entrypoint.sh /usr/local/bin/cron-entrypoint.sh
RUN chmod +x /usr/local/bin/cron-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/cron-entrypoint.sh"]
