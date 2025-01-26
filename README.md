# Nvidia Stock Bot
Par KevOut & Djeex

[![](https://img.shields.io/badge/JV%20hardware-rejoindre-green?style=flat-square&logo=discord&logoColor=%23fff&label=JV%20hardware&link=https%3A%2F%2Fdiscord.gg%2Fgxffg3GA96)](https://discord.gg/gxffg3GA96)


Ce robot :
- Appelle régulièrement l'api des stocks français de nvidia FE (par défaut toutes les 60s)
- Vérifie si RTX 5090, RTX 5080, RTX 5070ti et RTX 5070 sont en stock
- Si du stock est trouvé, envoie une notification discord via le webhook paramétré

<img src="https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/nvbot.png" align="center">

## Installation avec le dépot

### Pré-requis
- Git
- Docker

### Cloner et paramétrer

Clonez le repo :
```sh
git clone https://git.djeex.fr/Djeex/nvidia-stock-bot.git
```
Rendez-vous dans le dossier `nvidia-stock-bot/docker` et éditez le fichier `.env` avec :
- l'url de votre webhook discord
- la fréquence de consultation des stock (par défaut 60s, attention à ne pas trop descendre sous peine de blocage de votre adresse IP par nVidia)

### Lancer l'image

Rendez-vous dans le dossier `nvidia-stock-bot/docker` et lancez le conteneur :
```sh
docker compose up -d
```

### Voir les logs pour vérifier le bon fonctionnement

```sh
docker logs -f nvidia-stock-bot
```

## Si vous souhaitez compiler vous même

Rendez vous dans le dossier `nvidia-stock-bot` et compilez l'image docker :
```sh
docker build -t nvidia-stock-bot .
```

## Installation sans le dépot avec docker compose
Si vous ne souhaitez pas utiliser git pour cloner tout le dépot, une image docker à jour est mise à disposition dans ce registry.

### Pré-requis
- Docker

### Configuration

```yaml
version: "3.8"
services:
  nvidia-stock-bot:
    image: git.djeex.fr/djeex/nvidia-stock-bot:1
    container_name: nvidia-stock-bot
    restart: always # Le conteneur redémarrera automatiquement en cas d'échec
    environment:
      - DISCORD_WEBHOOK_URL= # URL de votre webhook Discord
      - REFRESH_TIME= # Durée de rafraichissement du script en secondes
      - PYTHONUNBUFFERED=1 # Permet d'afficher les logs en temps réel
    command: python nvidia-stock-bot.py # Lance le script Python au démarrage du conteneur
```