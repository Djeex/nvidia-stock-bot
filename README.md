# Nvidia Stock Bot
Par KevOut & Djeex

[![](https://img.shields.io/badge/JV%20hardware-rejoindre-green?style=flat-square&logo=discord&logoColor=%23fff&label=JV%20hardware&link=https%3A%2F%2Fdiscord.gg%2Fgxffg3GA96)](https://discord.gg/gxffg3GA96)


Ce robot :
- Appelle régulièrement l'api des stocks français de nvidia FE (par défaut toutes les 60s)
- Vérifie si RTX 5090, RTX 5080, RTX 5070ti et RTX 5070 sont en stock
- Si du stock est trouvé, envoie une notification discord via le webhook paramétré

<img src="https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/nvbot.png" align="center">


Trois modes d'installation :
- [Avec le dépot Git et Docker](https://git.djeex.fr/Djeex/nvidia-stock-bot/#installation-avec-le-d%C3%A9pot)
- [Sans le dépot Git et avec notre image docker fournie](https://git.djeex.fr/Djeex/nvidia-stock-bot/#installation-sans-le-d%C3%A9pot-avec-docker-compose)
- [Avec python (développeurs)](https://git.djeex.fr/Djeex/nvidia-stock-bot/#installation-sans-le-d%C3%A9pot-avec-docker-compose)

## Installation avec le dépot

Vous trouverez-ci dessous les instructions pour installer le dépot, compiler l'image docker, et lancer le conteneur. Avec cette solution, votre bot tournera tout seul tant que le conteneur est actif.

### Pré-requis
- Git
- Docker

### Cloner et paramétrer

Clonez le repo :
```sh
git clone https://git.djeex.fr/Djeex/nvidia-stock-bot.git
```

Rendez vous dans le dossier `nvidia-stock-bot` et compilez l'image docker :
```sh
docker build -t nvidia-stock-bot .
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

## Installation sans le dépot avec docker compose

Vous trouverez-ci dessous les instructions pour configurer le conteneur avec notre image pré-compilée. Avec cette solution, votre bot tournera tout seul tant que le conteneur est actif.

### Pré-requis
- Docker

### Configuration

```yaml
version: "3.8"
services:
  nvidia-stock-bot:
    image: git.djeex.fr/djeex/nvidia-stock-bot:6
    container_name: nvidia-stock-bot
    restart: always # Le conteneur redémarrera automatiquement en cas d'échec
    environment:
      - DISCORD_WEBHOOK_URL= # URL de votre webhook Discord
      - REFRESH_TIME= # Durée de rafraichissement du script en secondes
      - PYTHONUNBUFFERED=1 # Permet d'afficher les logs en temps réel
    command: python nvidia-stock-bot.py # Lance le script Python au démarrage du conteneur
```

## Installation avec Python

Vous trouverez ci-dessous comment exécuter directement le script Python. Avec cette solution, le bot s'arretera si vous fermez votre terminal.

### Pré-requis

- Python 3.11 ou plus
- requests : `pip install requests`

### Configuration

- Créez un environnement virtuel (exemple : `python3 -m venv nom_de_l_environnement` )
- Créez un dossier et aller dedans
- Téléchargez le script python :
  
  ```sh
  curl -o nvidia-stock-bot.py -# https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/nvidia-stock-bot.py
  ```
- Exportez les variables d'environnement avec votre webhook discord et le temps de rafraichissement en secondes, par exemple :
  
  ```sh
  export DISCORD_WEBHOOK_URL="https://votre_url_discord"
  export REFRESH_TIME="60"
  ```
- Lancez le script
  
  ```sh
  python nvidia-stock-bot.py
  ```