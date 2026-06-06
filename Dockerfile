FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --no-dev --no-install-project
COPY src/ src/
RUN uv sync --no-dev
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "neon.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
