FROM python:3.12-slim

# Install system dependencies required by uv
RUN apt-get update && \
    apt-get install -y curl git && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (system Python)
RUN uv sync --frozen --no-install-project --no-dev --python-preference=only-system

# Copy application code
COPY . .

# Expose the port your app uses (update if not 8000)
EXPOSE 8000

# Run the app using uv and uvicorn
CMD ["uv", "run", "uvicorn", "flowstate.app:app", "--host", "0.0.0.0", "--port", "8000"]
