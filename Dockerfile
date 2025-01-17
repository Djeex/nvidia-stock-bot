# Utiliser une image de base légère de Python (ici Python 3.9)
FROM python:3.9-slim

# Définir le répertoire de travail à l'intérieur du conteneur
WORKDIR /app

# Copier le script Python dans le répertoire de travail
COPY nvidia-stock-bot.py /app/

# Copier un éventuel fichier requirements.txt pour installer des dépendances
# Si des dépendances supplémentaires sont nécessaires, ajoutez-les dans requirements.txt
COPY requirements.txt /app/

# Installer les dépendances Python à partir de requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Définir les variables d'environnement par défaut (modifiable lors du lancement du conteneur)
ENV DISCORD_WEBHOOK_URL="https://example.com/webhook" \
    REFRESH_TIME="60"

# Exposer un point de commande pour exécuter le script
CMD ["python", "bot_nvidia.py"]