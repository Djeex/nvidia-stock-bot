FROM python:3.14.7-alpine AS base

RUN apk add --no-cache ca-certificates

WORKDIR /app

COPY VERSION /VERSION
COPY /app/ /app/

RUN pip install --no-cache-dir -r requirements.txt

FROM base AS test

RUN pip install --no-cache-dir pytest==9.1.1

COPY pytest.ini /app/pytest.ini
COPY /tests/ /app/tests/

CMD ["pytest", "-v"]

FROM base

RUN addgroup -g 911 nvbot && adduser -D -u 911 -G nvbot nvbot

USER nvbot

CMD ["python", "main.py"]
