FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY core/ core/
COPY bot/ bot/
COPY migrations/ migrations/

RUN pip install --no-cache-dir .

COPY entrypoint.sh alembic.ini ./
RUN chmod +x entrypoint.sh

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

ENTRYPOINT ["./entrypoint.sh"]
