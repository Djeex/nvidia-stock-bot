FROM python:3.11-alpine

RUN apk add --no-cache ca-certificates

WORKDIR /app

COPY nvidia-stock-bot.py /app/

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

ENV DISCORD_WEBHOOK_URL="https://example.com/webhook" \
    REFRESH_TIME="30"

CMD ["python", "nvidia-stock-bot.py"]