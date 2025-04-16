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
RUN uv venv
COPY pyproject.toml ./
RUN uv pip install -r ./pyproject.toml

# Copy application code and migration files
COPY ./src ./src
COPY ./main.py ./main.py
COPY ./tracked_repos ./tracked_repos
COPY ./migrations ./migrations
