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
>_Github repo is a mirror of https://git.djeex.fr/Djeex/nvidia-stock-bot. You'll find full package, history and release note there. LLM used for bugs check and languages files generation._

## 🖼️ Screenshots

<div align="center" >
  <img src="https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/nvidia-stock-bot-discord-screenshot.png" alt="Nvidia Stock Bot - screenshots">
</div>

## 📌 Table of Contents

- [✨ Features](#-features)
- [🐳 Docker Installation without cloning the repo (quick)](#-docker-installation-without-the-repo-quick)
- [🐙 Docker Installation with the repo (developer)](#-docker-installation-with-the-repo)
- [🐍 Python Installation (developer)](#-python-installation)
- [🐞 Common issues](#-common-issues)
- [❓ How it works](#-how-it-works)
- [🧑‍💻 Contributors](#-contributors)

## ✨ Features

- Selectable GPU models
- Selectable country marketplace to check. It will set notifications language and currency accordingly
- Discord `@everyone` or specified role on SKU change (possible imminent drop)
- Discord `@everyone` or specified role notification when stock is detected, including model, price, and link
- Silent Discord notification when no stock is detected
- Selectable notification server name in notification footer
- Selectable check frequency
- Test mode to check without sending notifications

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
      - PRODUCT_NAMES=                  # Exact GPU name (e.g. 'RTX 5080, RTX 5090')
      - DISCORD_WEBHOOK_URL=            # Your Discord webhook URL
      - COUNTRY=                        # Set your country (e.g. 'US')
      - PYTHONUNBUFFERED=1              # Enables real-time log output
```

**Environment Variables:**

| Variable            | Description                                     | Possible Values                                                  | Default Value                                                                                              |
|---------------------|-------------------------------------------------|------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| `PRODUCT_NAMES`        | The exact GPU names you're searching for         | `RTX 5080, RTX 5090`                             |                                                                                                             |
| `DISCORD_WEBHOOK_URL` | Your Discord webhook URL                        | A valid URL                                                     |                                                                                                              |
| `COUNTRY` | Your country (only one). API localization, Discord notification currency and language will be set accordingly                    | `GB`, `US`, `CA`, `BE`, `NL`, `DK`, `DE`, `ES`, `FR`, `IT`, `NO`, `AT`, `PL`, `FI`, `SE`, `KR`, `JP` | `US` |
| `DISCORD_SERVER_NAME`        | The name of your server, displayed in notification's footer         | A text                             | Shared for free                                                                                                            |
| `DISCORD_ROLES` | List of Discord roles ID in the same order than `PRODUCT_NAMES` values, found in your discord server settings (with user profile developer mode enabled)                         | `<@&12345><@&6789>`                                                    | @everyone                                                                                                            |
| `REFRESH_TIME`        | Script refresh interval in seconds              | `60`, `30`, etc.                                                 | `30`                                                                                                        |
| `API_URL_SKU`         | API listing the product. Use it for development purpose. __Warning__ : it will override the locale set by `COUNTRY`.                     | An URL | `https://api.nvidia.partners/edge/product/search?page=1&limit=100&locale={locale}&Manufacturer=Nvidia`         |
| `API_URL_STOCK`       | API providing stock data.  Use it for development purpose. __Warning__ : it will override the locale set by `COUNTRY`.                        | A URL | `https://api.store.nvidia.com/partner/v1/feinventory?locale={locale}&skus=`                                    |
| `PRODUCT_URL`         | GPU purchase URL. Use it for development purpose. __Warning__ : it will override the locale set by `COUNTRY`.                              | A URL | `https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale={locale}&page=1&limit=12&manufacturer=NVIDIA` |
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
export COUNTRY=US
export PRODUCT_NAMES=RTX 5080, RTX 5090
export DISCORD_ROLES=<@&12345>, <@&6789>
export REFRESH_TIME="60"
export TEST_MODE=false
export PYTHONUNBUFFERED=1
```

- Run the script

```sh
python nvidia-stock-bot.py
```

## 🐞 Common issues

Error when trying to reach product API url :
- Custom `API_SKU_URL` may be wrong
- Your IP may be blacklisted by nvidia. Try to use a VPN.
- nvidia API may be down

## ❓ How it works

<div align="center" >
  <img src="https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/nvidia-stock-bot-scheme.svg" alt="Nvidia Stock Bot - screenshots">
</div>

## 🧑‍💻 Contributors

Thanks for their contributions:

- Djeex
- KevOut
- Extreme2pac