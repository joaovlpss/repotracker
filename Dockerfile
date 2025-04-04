FROM python:3.12 as base

# Set environment variables
# Prevents python creating .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# Prevents python buffering stdout/stderr
ENV PYTHONUNBUFFERED 1
# Uv version 
ENV UV_VERSION 0.6.12

WORKDIR /app

# Install uv
RUN pip install uv==${UV_VERSION}

FROM base as builder

# Copy and build dependencies from pyproject.toml
COPY pyproject.toml ./
RUN uv pip install --system --no-cache .[dev]

# Final stage: Copy dependencies and code
FROM base as final

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python*/site-packages/ /usr/local/lib/python*/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY ./src ./src
COPY ./main.py ./main.py
COPY ./tracked_repos ./tracked_repos

ENTRYPOINT ["python", "main.py"]