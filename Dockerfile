FROM python:3.11-slim-bookworm AS builder
WORKDIR /app
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    rm -rf /var/lib/apt/lists/*
COPY requirements-prod.txt .
RUN pip install --user --no-cache-dir -r requirements-prod.txt

FROM python:3.11-slim-bookworm AS runner
WORKDIR /app
RUN groupadd -r geo && useradd -r -g geo geo
COPY --from=builder /root/.local /home/geo/.local
COPY . .
RUN chown -R geo:geo /app
USER geo
ENV PATH=/home/geo/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "geo_audit_agent.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
