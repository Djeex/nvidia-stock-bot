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

- [✨ Features](#-features)
- [🐳 Docker Installation without cloning the repo (quick)](#-docker-installation-without-the-repo-quick)
- [🐙 Docker Installation with the repo (developer)](#-docker-installation-with-the-repo)
- [🐍 Python Installation (developer)](#-python-installation)
- [🖼️ Screenshots](#-screenshots)
- [🐞 Common issues](#-common-issues)
- [🧑‍💻 Contributors](#-contributors)

## ✨ Features

- Selectable GPU models
- Discord `@everyone` or specified role on SKU change (possible imminent drop)
- Discord `@everyone` or specified role notification when stock is detected, including model, price, and link
- Silent Discord notification when no stock is detected
- Selectable notification language
- Selectable notification server name in footer
- Selectable check frequency

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
    # Minimal environment variables
      - PRODUCT_NAMES=                  # Exact GPU name (e.g. "RTX 5080, RTX 5090")
      - DISCORD_WEBHOOK_URL=            # Your Discord webhook URL
      - DISCORD_NOTIFICATION_CURRENCY=  # Set your country currency
      - API_URL_SKU=                    # API listing the product for your country
      - API_URL_STOCK=                  # API providing stock data for your country
      - PRODUCT_URL=                    # GPU purchase URL for your country
      - PYTHONUNBUFFERED=1              # Enables real-time log output
```

**Environment Variables:**

| Variable            | Description                                     | Possible Values                                                  | Default Value                                                                                              |
|---------------------|-------------------------------------------------|------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| `PRODUCT_NAMES`        | The exact GPU names you're searching for         | `RTX 5080, RTX 5090`                             |                                                                                                             |
| `DISCORD_WEBHOOK_URL` | Your Discord webhook URL                        | A valid URL                                                     |                                                                                                              |
| `DISCORD_NOTIFICATION_CURRENCY` | Your country currency                        | A text, e.g. `$`, `€`, `£`...                                                      | `€`                                                                                                                 |
| `DISCORD_SERVER_NAME`        | The name of your server, displayed in notification's footer         | A text                             | Shared for free                                                                                                            |
| `DISCORD_NOTIFICATION_LANGUAGE` | Your language for notification's content                        | `bg`, `cs`, `da`, `de`, `el`, `en`, `es`, `et`, `fi`, `fr`, `ga`, `hr`, `hu`, `it`, `lt`, `lv`, `mt`, `nl`, `pl`, `pt`, `ro`, `sk`, `sl`, `sv`                                                      | `en`                                                                                                             |
| `DISCORD_ROLES` | List of Discord roles ID in the same order than `PRODUCT_NAMES` values, found in your discord server settings (with user profile developer mode enabled)                         | `<@&12345><@&6789>`                                                    | @everyone                                                                                                            |
| `REFRESH_TIME`        | Script refresh interval in seconds              | `60`, `30`, etc.                                                 | `30`                                                                                                        |
| `API_URL_SKU`         | API listing the product                         | A URL. API url can change over time. For now, you can use the default one and change the `locale` parameter to yours (e.g. `locale=en-gb`)                                                            | `https://api.nvidia.partners/edge/product/search?page=1&limit=100&locale=fr-fr&Manufacturer=Nvidia`         |
| `API_URL_STOCK`       | API providing stock data                        | A URL. API url can change over time. For now, you can use the default one and change the `locale` parameter to yours (e.g. `locale=en-gb`)                                                                  | `https://api.store.nvidia.com/partner/v1/feinventory?locale=fr-fr&skus=`                                    |
| `PRODUCT_URL`         | GPU purchase URL. There isn't any direct link workinf right now, so put the generic marketplace url listing all FE products                              | A URL. API url can change over time. For now, you can use the default one and change the locale parameter to yours (e.g. `/en-gb/`)                                                                  | `https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&page=1&limit=12&manufacturer=NVIDIA` |
| `TEST_MODE`           | For testing without sending notifications       | `True`, `False`                                                  | `False`                                                                                                     |
| `PYTHONUNBUFFERED`    | Enables real-time log output                    | `1`, `0`                                                         | `1`                                                                                                         |

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
export DISCORD_NOTIFICATION_CURRENCY=€
export PRODUCT_NAMES=RTX 5080, RTX 5090
export DISCORD_ROLES=<@&12345>, <@&6789>
export REFRESH_TIME="60"
export API_URL_SKU="https://api.nvidia.partners/edge/product/search?page=1&limit=100&locale=fr-fr&Manufacturer=Nvidia&gpu=RTX%205080"
export API_URL_STOCK="https://api.store.nvidia.com/partner/v1/feinventory?locale=fr-fr&skus="
export PRODUCT_URL="https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&page=1&limit=12&gpu=RTX%205080&manufacturer=NVIDIA"
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

## 🐞 Common issues

Error when trying to reach product API url :
- `API_SKU_URL` may be wrong
- Your IP may be blacklisted by nvidia. Try to use a VPN.
- nvidia API may be down

## 🧑‍💻 Contributors

Thanks for their contributions:

- Djeex
- KevOut
- Extreme2pac