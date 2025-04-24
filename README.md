<h1 align="center">Nvidia Stock Bot</h1>
<div align="center">
    <a href="https://discord.gg/gxffg3GA96">
        <img src="https://img.shields.io/badge/JV%20hardware-rejoindre-green?style=flat-square&logo=discord&logoColor=%23fff" alt="JV Hardware">
    <a href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank">
        <img src="https://img.shields.io/badge/License-CC%20BY--NC%204.0-8E44AD?style=flat-square" alt="License: CC BY-NC 4.0">
    </a>

</div>
<div align="center" >
    <img src="https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/nvidia-stock-bot-logo.png" alt="Nvidia Stock Bot" width="300">
</div>

**🤖 Nvidia Stock Bot** - Un robot qui permet d'être alerté en temps réel des stocks de cartes graphiques **Nvidia RTX FE** grâce à des notifications Discord.

*Le code a été en partie rédigé et structuré à l'aide d'une IA générative.*

## 📌 Sommaire

- [✨ Fonctionnalités](#fonctionnalit%C3%A9s)
- [🐳 Installation docker sans le dépot (rapide)](#installation-sans-le-d%C3%A9pot-avec-docker-compose)
- [🐙 Installation docker avec le dépot (développeur)](#installation-avec-le-d%C3%A9pot)
- [🐍 Installation avec Python (développeur)](#installation-avec-python)
- [🖼️ Captures d'écran](#captures-d%C3%A9cran)
- [🧑‍💻 Contributeurs](#contributeurs)

## ✨ Fonctionnalités

- Notification Discord `@everyone` en cas de changement du SKU (potentiel drop imminent)
- Notification Discord `@everyone` en cas de stock détecté avec modèle, prix, et lien
- Notification Discord silencieuse en cas d'absence de stock détécté
- Choix de la fréquence de la vérification
- Choix du modèle à surveiller

<img src="https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/nvbot_schematics.png" align="center">

## 🐳 Installation sans le dépot avec docker compose

Vous trouverez-ci dessous les instructions pour configurer le conteneur avec notre image pré-compilée. Avec cette solution, votre bot tournera tout seul tant que le conteneur est actif.

**Pré-requis**
- [Docker](https://docs.docker.com/engine/install/)

**Configuration**

- Créez un dossier `nvidia-stock-bot`
- Créez le fichier `compose.yaml` dans ce dossier avec la configuration ci-dessous :

```yaml
services:
  nvidia-stock-bot:
    image: git.djeex.fr/djeex/nvidia-stock-bot:latest
    container_name: nvidia-stock-bot
    restart: unless-stopped
    environment:
      - DISCORD_WEBHOOK_URL= # URL de votre webhook Discord
      - PRODUCT_NAME=        # Le nom exact du GPU que vous recherchez comme "RTX 5080"
      - PYTHONUNBUFFERED=1   # Permet d'afficher les logs en temps réel
    command: python nvidia-stock-bot.py
```

**Variables d'environnements :**

| Variables           | Explications                                    | Valeurs possibles                                                  | Valeur par défaut                                                                                              |
|---------------------|-------------------------------------------------|--------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| DISCORD_WEBHOOK_URL | URL de votre webhook Discord                    | Une URL                       |                                                                                                                |
| REFRESH_TIME        | Durée de rafraichissement du script en secondes | `60`, `30`, etc...                                                     | `30`                                                                                                             |
| API_URL_SKU         | API listant le produit                          | Une URL                     | `https://api.nvidia.partners/edge/product/search?page=1&limit=100&locale=fr-fr&Manufacturer=Nvidia`              |
| API_URL_STOCK       | API donnant le stock                            | Une URL        | `https://api.store.nvidia.com/partner/v1/feinventory?locale=fr-fr&skus=`                                         |
| PRODUCT_URL         | URL d'achat du GPU                              | Une URL | `https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&page=1&limit=12&manufacturer=NVIDIA` |
| PRODUCT_NAME        | Le nom exact du GPU que vous recherchez         | `RTX 5090`, `RTX 5080` ou `RTX 5070`.                                    |                                                                                                                |
| TEST_MODE           | Pour tester sans envoyer de notifs              | `True`, `False`                                                        | `False`                                                                                                          |
| PYTHONUNBUFFERED    | #Permet d'afficher les logs en temps réel       | `1`, `0`                                                               | `1`                                                                                                              |

**Lancer l'image**

Rendez-vous dans le dossier `nvidia-stock-bot` et lancez le conteneur :
```sh
docker compose up -d
```

**Voir les logs pour vérifier le bon fonctionnement**

```sh
docker logs -f nvidia-stock-bot
```

## 📦 Installation avec le dépot

Vous trouverez-ci dessous les instructions pour installer le dépot, compiler l'image docker, et lancer le conteneur. Avec cette solution, votre bot tournera tout seul tant que le conteneur est actif.

**Pré-requis**
- [Git](https://git-scm.com/docs)
- [Docker](https://docs.docker.com/engine/install/)

**Cloner et paramétrer**

- Clonez le repo :
```sh
git clone https://git.djeex.fr/Djeex/nvidia-stock-bot.git
```

- Rendez vous dans le dossier `nvidia-stock-bot` et compilez l'image docker :
```sh
docker build -t nvidia-stock-bot .
```

- Puis rendez-vous dans le dossier `nvidia-stock-bot/docker` et éditez le fichier `.env` avec :
  - l'url de votre webhook discord
  - les différents liens API et produits
  - la fréquence de consultation des stock (par défaut 60s, attention à ne pas trop descendre sous peine de blocage de votre adresse IP par nVidia)

**Lancer l'image**

Rendez-vous dans le dossier `nvidia-stock-bot/docker` et lancez le conteneur :
```sh
docker compose up -d
```

**Voir les logs pour vérifier le bon fonctionnement**

```sh
docker logs -f nvidia-stock-bot
```

## 🐍 Installation avec Python

Vous trouverez ci-dessous comment exécuter directement le script Python. Avec cette solution, le bot s'arretera si vous fermez votre terminal.

**Pré-requis**

- Python 3.11 ou plus
- requests : `pip install requests`

**Configuration**

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
  export API_URL_SKU="https://api.nvidia.partners/edge/product/search?page=1&limit=100&locale=fr-fr&Manufacturer=Nvidia&gpu=RTX%205080"
  export API_URL_STOCK="https://api.store.nvidia.com/partner/v1/feinventory?locale=fr-fr&skus="
  export PRODUCT_URL= "https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&page=1&limit=12&gpu=RTX%205080&manufacturer=NVIDIA"
  export PRODUCT_NAME="RTX 5080"
  export TEST_MODE=false
  ```
- Lancez le script
  
  ```sh
  python nvidia-stock-bot.py
  ```

## 🖼️ Captures d'écran

  <div align="center" >
    <img src="https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/nvidia-stock-bot-discord.png" alt="Nvidia Stock Bot - captures">
</div>

## 🧑‍💻 Contributeurs

On remercie pour leurs contributions :

- Djeex
- KevOut
- Extreme2pac