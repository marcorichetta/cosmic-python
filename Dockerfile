FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.8.4 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen


RUN mkdir -p /src
COPY src/ src/
# Add --no-deps since deps already installed
RUN uv pip install --no-deps -e src/ 
COPY tests/ tests/

ENV FLASK_APP=src/allocation/entrypoints/flask_app.py FLASK_DEBUG=1 PYTHONUNBUFFERED=1
CMD uv run flask run --host=0.0.0.0 --port=80