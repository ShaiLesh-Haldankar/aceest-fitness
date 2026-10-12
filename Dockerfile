# ---------- Stage 1: build wheels for runtime dependencies ----------
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---------- Stage 2: test image (runtime + pytest), used by CI ----------
FROM python:3.12-slim AS test
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
CMD ["python", "-m", "pytest", "-q"]

# ---------- Stage 3: slim, non-root production image ----------
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ACEEST_DB=/app/data/aceest_fitness.db \
    PORT=5000
WORKDIR /app
RUN groupadd --system aceest && useradd --system --gid aceest --no-create-home aceest
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
COPY app.py db.py fitness.py ./
COPY templates ./templates
RUN mkdir -p /app/data && chown -R aceest:aceest /app/data
USER aceest
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:create_app()"]
