FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY src/ /app/src
COPY main.py /app/
COPY scrape_reddit_trends.py /app/

# Créer le répertoire data
RUN mkdir -p /app/data

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:server"]

