FROM python:3.11.2-slim as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

WORKDIR /app

FROM base as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.6.1

RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock README.md log.conf ./
COPY ledger_bot ./ledger_bot
COPY logs ./logs

RUN poetry config virtualenvs.in-project true && \
    poetry install --only=main --no-root && \
    poetry build

CMD [ "poetry", "run", "python", "-m", "ledger_bot"]