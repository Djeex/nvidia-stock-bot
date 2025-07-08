<h1 align="center">Nvidia Stock Bot</h1>
<div align="center">
    <a href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank">
        <img src="https://img.shields.io/badge/License-CC%20BY--NC%204.0-8E44AD?style=flat-square" alt="License: CC BY-NC 4.0">
    </a>
</div>
<div align="center" >
    <img src="https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/nvidia-stock-bot-logo.png" alt="Nvidia Stock Bot" width="300">
</div>

**🤖 Nvidia Stock Bot** - A bot that alerts you in real-time about **Nvidia RTX FE** GPU stock availability through Discord notifications.

> [!NOTE]
>_The code was partially written and structured using a generative AI._
>
>_Github repo is a mirror of https://git.djeex.fr/Djeex/nvidia-stock-bot. You'll find full package, history and release note there._

## 📌 Table of Contents

- [✨ Features](#features)
- [🐳 Docker Installation without cloning the repo (quick)](#docker-installation-without-the-repo-quick)
- [🐙 Docker Installation with the repo (developer)](#docker-installation-with-the-repo)
- [🐍 Python Installation (developer)](#python-installation)
- [🖼️ Screenshots](#screenshots)
- [🧑‍💻 Contributors](#contributors)

## ✨ Features

- Discord `@everyone` notification on SKU change (possible imminent drop)
- Discord `@everyone` notification when stock is detected, including model, price, and link
- Silent Discord notification when no stock is detected
- Selectable check frequency
- Selectable GPU model

## 🐳 Docker Installation without the repo (quick)

Below are the instructions to set up the container using our pre-built image. With this setup, your bot will run independently as long as the container is active.

**Requirements**
- [Docker](https://docs.docker.com/engine/install/)

**Configuration**

- Create a folder named `nvidia-stock-bot`
- Create a `compose.yaml` file inside that folder with the following content:

```yaml
services:
  nvidia-stock-bot:
    image: git.djeex.fr/djeex/nvidia-stock-bot:latest
    container_name: nvidia-stock-bot
    restart: unless-stopped
    environment:
      - DISCORD_WEBHOOK_URL= # Your Discord webhook URL
      - PRODUCT_NAME=        # Exact GPU name like "RTX 5080"
      - API_URL_SKU=         # API listing the product
      - API_URL_STOCK=       # API providing stock data
      - PRODUCT_URL=         # GPU purchase URL

      - PYTHONUNBUFFERED=1   # Enables real-time log output
    command: python nvidia-stock-bot.py
```

**Environment Variables:**

| Variable            | Description                                     | Possible Values                                                  | Default Value                                                                                              |
|---------------------|-------------------------------------------------|------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| DISCORD_WEBHOOK_URL | Your Discord webhook URL                        | A valid URL                                                      |                                                                                                             |
| DISCORD_ROLE | Role ID, found in your discord server settings (with developer mode enabled)                         | <@&123456789>                                                      | @everyone                                                                                                            |
| REFRESH_TIME        | Script refresh interval in seconds              | `60`, `30`, etc.                                                 | `30`                                                                                                        |
| API_URL_SKU         | API listing the product                         | A URL. API url can change over time. For now, you can use the default one and change the `locale` parameter to yours (for exemple : `locale=en-gb`)                                                            | `https://api.nvidia.partners/edge/product/search?page=1&limit=100&locale=fr-fr&Manufacturer=Nvidia`         |
| API_URL_STOCK       | API providing stock data                        | A URL. API url can change over time. For now, you can use the default one and change the `locale` parameter to yours (for exemple : `locale=en-gb`)                                                                  | `https://api.store.nvidia.com/partner/v1/feinventory?locale=fr-fr&skus=`                                    |
| PRODUCT_URL         | GPU purchase URL                                | A URL. API url can change over time. For now, you can use the default one and change the `locale` parameter to yours (for exemple : `/en-gb/`)                                                                  | `https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&page=1&limit=12&manufacturer=NVIDIA` |
| PRODUCT_NAME        | The exact GPU name you're searching for         | `RTX 5090`, `RTX 5080`, `RTX 5070`                               |                                                                                                             |
| TEST_MODE           | For testing without sending notifications       | `True`, `False`                                                  | `False`                                                                                                     |
| PYTHONUNBUFFERED    | Enables real-time log output                    | `1`, `0`                                                         | `1`                                                                                                         |

**Run the image**

Navigate to the `nvidia-stock-bot` folder and launch the container:
```sh
docker compose up -d
```

**Check logs to verify operation**

```sh
docker logs -f nvidia-stock-bot
```

## 📦 Docker Installation with the repo

Instructions below show how to install the repo, build the Docker image, and launch the container. Your bot will run independently as long as the container is active.

**Requirements**
- [Git](https://git-scm.com/docs)
- [Docker](https://docs.docker.com/engine/install/)

**Clone and configure**

- Clone the repo:
```sh
git clone https://git.djeex.fr/Djeex/nvidia-stock-bot.git
```

- Navigate to `nvidia-stock-bot` and build the Docker image:
```sh
docker build -t nvidia-stock-bot .
```

- Then go to `nvidia-stock-bot/docker` and edit the `.env` file with:
  - Your Discord webhook URL
  - The API and product URLs
  - Stock checking frequency (default: 60s; lowering too much may get your IP blocked by Nvidia)

**Run the image**

Navigate to `nvidia-stock-bot/docker` and launch the container:
```sh
docker compose up -d
```

**Check logs to verify operation**

```sh
docker logs -f nvidia-stock-bot
```

## 🐍 Python Installation

Instructions to directly run the Python script. Note: the bot stops when you close the terminal.

**Requirements**

- Python 3.11 or newer
- requests: `pip install requests`

**Configuration**

- Clone the repo:

```sh
git clone https://git.djeex.fr/Djeex/nvidia-stock-bot.git
```
- Navigate to `nvidia-stock-bot` and create a virtual environment (e.g., `python3 -m venv env_name`)
- Export the environment variables with your webhook and refresh time, for exemple:

```sh
export DISCORD_WEBHOOK_URL="https://your_discord_url"
export DISCORD_ROLE="<@&123456789>"
export REFRESH_TIME="60"
export API_URL_SKU="https://api.nvidia.partners/edge/product/search?page=1&limit=100&locale=fr-fr&Manufacturer=Nvidia&gpu=RTX%205080"
export API_URL_STOCK="https://api.store.nvidia.com/partner/v1/feinventory?locale=fr-fr&skus="
export PRODUCT_URL="https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&page=1&limit=12&gpu=RTX%205080&manufacturer=NVIDIA"
export PRODUCT_NAME="RTX 5080"
export TEST_MODE=false
export PYTHONUNBUFFERED=1
```

- Run the script

```sh
python nvidia-stock-bot.py
```

## 🖼️ Screenshots

<div align="center" >
  <img src="https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/nvidia-stock-bot-discord.png" alt="Nvidia Stock Bot - screenshots">
</div>

## 🧑‍💻 Contributors

Thanks for their contributions:

- Djeex
- KevOut
- Extreme2pac