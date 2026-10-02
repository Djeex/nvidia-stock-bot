FROM python:3.14.8-alpine AS base

RUN apk add --no-cache ca-certificates

WORKDIR /app

COPY VERSION /VERSION
COPY /app/ /app/

RUN pip install --no-cache-dir -r requirements.txt

FROM base AS test

RUN pip install --no-cache-dir pytest==9.1.1 pytest-cov==7.1.0

COPY pytest.ini /app/pytest.ini
COPY /tests/ /app/tests/

CMD ["pytest", "-v"]

FROM base AS lint

RUN pip install --no-cache-dir ruff==0.16.4
COPY ruff.toml /app/ruff.toml
COPY /tests/ /app/tests/
RUN ruff check . && ruff format --check .

FROM base

RUN addgroup -g 911 nvbot && adduser -D -u 911 -G nvbot nvbot

USER nvbot

CMD ["python", "main.py"]
