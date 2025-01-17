# Nvidia Stock Bot
Par KevOut & Djeex

Ce robot :
- Appelle régulièrement l'api des stocks français de nvidia FE (par défaut toutes les 60s)
- Vérifie si RTX 5090, RTX 5080, RTX 5070ti et RTX 5070 sont en stock
- Si du stock est trouvé, envoie une notification discord via le webhook paramétré

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
