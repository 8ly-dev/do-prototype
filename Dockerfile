FROM python:3.12-slim

# Refresh the OS store independently of the base image cache (eMudhra distrust).
RUN apt-get update \
    && apt-get install -y --no-install-recommends --only-upgrade ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.13.4 /uv /uvx /usr/local/bin/
RUN python -I -c 'import ssl, hashlib; certs = ssl.create_default_context().get_ca_certs(binary_form=True); assert len(certs) > 50; assert "86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b" not in {hashlib.sha256(c).hexdigest() for c in certs}'

# Install system dependencies required by uv
RUN apt-get update && \
    apt-get install -y curl git && \
    rm -rf /var/lib/apt/lists/*

# Install uv

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (system Python)
RUN uv sync --frozen --no-install-project --no-dev --python-preference=only-system
RUN .venv/bin/python -I -c 'import ssl, certifi, hashlib; ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT); ctx.load_verify_locations(certifi.where()); certs = ctx.get_ca_certs(binary_form=True); assert len(certs) > 50; assert "86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b" not in {hashlib.sha256(c).hexdigest() for c in certs}'

# Copy application code
COPY . .

# Expose the port your app uses (update if not 8000)
EXPOSE 8000

# Run the app using uv and uvicorn
CMD ["uv", "run", "uvicorn", "do.app:app", "--host", "0.0.0.0", "--port", "8000"]
