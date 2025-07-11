FROM python:3.11-alpine

RUN apk add --no-cache ca-certificates

WORKDIR /app

COPY /app/ /app/

RUN pip install --no-cache-dir -r requirements.txt

ENV DISCORD_WEBHOOK_URL="https://example.com/webhook" \
    REFRESH_TIME="30"

CMD ["python", "main.py"]