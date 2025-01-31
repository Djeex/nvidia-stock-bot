import requests
import logging
import time
import os

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logging.info("Démarrage du script")

# Récupération des variables d'environnement
try:
    DISCORD_WEBHOOK_URL = os.environ['DISCORD_WEBHOOK_URL']
    REFRESH_TIME = int(os.environ['REFRESH_TIME'])  # Convertir en entier
except KeyError as e:
    logging.error(f"Variable d'environnement manquante : {e}")
    exit(1)  # Quitter le script proprement en cas d'erreur
except ValueError:
    logging.error("REFRESH_TIME doit être un entier valide.")
    exit(1)

# Afficher les valeurs des variables d'environnement
print(f"url du webhook Discord: {DISCORD_WEBHOOK_URL}")
print(f"Temps d'actualisation (en secondes) : {REFRESH_TIME}")

# L’URL de l’API (exemple)
API_URL = "https://api.nvidia.partners/edge/product/search?page=1&limit=9&locale=fr-fr&category=GPU&gpu=RTX%205080,RTX%205090"

# GPUs à surveiller
GPU_TARGETS = ["RTX 5070 Ti", "RTX 5070", "RTX 5080", "RTX 5090"]

# Entêtes HTTP pour la requête
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.5",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Sec-GPC": "1",
}

# Dictionnaire stockant l'état de stock
stock_status = {gpu.upper(): False for gpu in GPU_TARGETS}

session = requests.Session()

def send_discord_notification(gpu_name: str, product_link: str):
    """Envoie une notification Discord avec un embed via un webhook."""
    embed = {
        "title": f"🚀 {gpu_name} en stock !",
        "description": f":point_right: **[Achetez ici](https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&page=1&limit=12&gpu=RTX%205090,RTX%205080&manufacturer=NVIDIA)**",
        "color": 3066993,  # Couleur verte
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        #"thumbnail": {
        #    "url": "https://www.nvidia.com/content/dam/en-zz/Solutions/geforce/graphic-cards/50-series/rtx-5090/geforce-rtx-5090-learn-more-og-1200x630.jpg"
        #}
    }

    payload = {
        "content": "@everyone",
        "username": "Nvidia Bot",
        "embeds": [embed]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("✅ Embed envoyé sur Discord.")
        else:
            logging.error(f"❌ Erreur d'envoi du webhook : {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"🚨 Erreur lors de l'envoi du webhook : {e}")

def check_rtx_50_founders():
    """Vérifie l'état de stock des GPU Founders Edition et notifie Discord si un GPU repasse en stock."""
    try:
        response = session.get(API_URL, headers=HEADERS, timeout=10)
        logging.info(f"Réponse de l'API : {response.status_code}")
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur lors de l'appel API : {e}")
        return

    products = data.get("searchedProducts", {}).get("productDetails", [])
    found_in_stock = set()

    for p in products:
        gpu_name = p.get("gpu", "").upper()
        is_founder = p.get("isFounderEdition") is True
        is_nvidia = (p.get("manufacturer") == "NVIDIA")
        is_buy_now = (p.get("prdStatus") != "out_of_stock")

        if is_founder and is_nvidia and is_buy_now:
            if any(target.upper() in gpu_name for target in GPU_TARGETS):
                found_in_stock.add(gpu_name)

    for gpu in GPU_TARGETS:
        gpu_upper = gpu.upper()
        currently_in_stock = (gpu_upper in found_in_stock)
        previously_in_stock = stock_status[gpu_upper]

        if currently_in_stock and not previously_in_stock:
            for product in products:
                product_name = product.get("gpu", "").upper()
                if product_name == gpu_upper:
                    real_gpu_name = product.get("gpu", "Inconnu")
                    product_link = "https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&page=1&limit=12&gpu=RTX%205090,RTX%205080"
                    send_discord_notification(real_gpu_name, product_link)

            stock_status[gpu_upper] = True
            print(f"{gpu} est maintenant en stock!")

        elif (not currently_in_stock) and previously_in_stock:
            logging.info(f"{gpu} n'est plus en stock.")
            stock_status[gpu_upper] = False
            print(f"{gpu} est hors stock !")
        
        elif not currently_in_stock:
            print(f"{gpu} est actuellement hors stock.")

if __name__ == "__main__":
    while True:
        check_rtx_50_founders()
        time.sleep(REFRESH_TIME)
