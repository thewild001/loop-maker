FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LOOP_MAKER_DB=/data/loop-maker.sqlite3

WORKDIR /app

RUN groupadd --system --gid 10001 loopmaker \
    && useradd --system --uid 10001 --gid loopmaker --home-dir /app loopmaker \
    && mkdir -p /data \
    && chown loopmaker:loopmaker /data

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir ".[mcp]" \
    && python -m pip cache purge

USER loopmaker

VOLUME ["/data"]

ENTRYPOINT ["loop-maker-mcp"]
