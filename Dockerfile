FROM python:3.13-alpine

RUN apk add --no-cache ca-certificates

WORKDIR /app

COPY /app/ /app/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]