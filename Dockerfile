FROM --platform=linux/amd64 python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get upgrade -y && apt-get clean && rm -rf /var/lib/apt/lists

RUN useradd -m me
USER me
WORKDIR /home/me

COPY uv.lock pyproject.toml ./
COPY --chown=me wuzzln/ wuzzln/
COPY --chown=me templates/ templates/
COPY --chown=me assets/ assets/

CMD uv run --no-dev litestar --app wuzzln.app:app run --port 8501 --host 0.0.0.0
