import requests
import logging
import time
import os
import re
from requests.adapters import HTTPAdapter, Retry

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logging.info("Démarrage du script")

# Récupération des variables d'environnement
try:
    DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
    API_URL_SKU = os.environ.get('API_URL_SKU', 'https://api.nvidia.partners/edge/product/search?page=1&limit=100&locale=fr-fr&Manufacturer=Nvidia')
    API_URL_STOCK = os.environ.get('API_URL_STOCK', 'https://api.store.nvidia.com/partner/v1/feinventory?locale=fr-fr&skus=')
    REFRESH_TIME = int(os.environ.get('REFRESH_TIME'))
    TEST_MODE = os.environ.get('TEST_MODE', 'False').lower() == 'true'
    PRODUCT_URL = os.environ.get('PRODUCT_URL', 'https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&page=1&limit=12&manufacturer=NVIDIA')
    PRODUCT_NAME = os.environ.get('PRODUCT_NAME')
    
    # Logging des erreurs
    if not DISCORD_WEBHOOK_URL:
        logging.error("❌ DISCORD_WEBHOOK_URL est requis mais non défini.")
        exit(1)

    if not PRODUCT_NAME:
        logging.error("❌ PRODUCT_NAME est requis mais non défini.")
        exit(1)

    # Regex pour extraire l'ID et le token
    match = re.search(r'/(\d+)/(.*)', DISCORD_WEBHOOK_URL)
    if match:
        webhook_id = match.group(1)
        webhook_token = match.group(2)

        # Masquer derniers caractères de l'ID
        masked_webhook_id = webhook_id[:len(webhook_id) - 10] + '*' * 10

        # Masquer derniers caractères du token
        masked_webhook_token = webhook_token[:len(webhook_token) - 120] + '*' * 10

        # Reconstruction de l'url masquée
        wh_masked_url = f"https://discord.com/api/webhooks/{masked_webhook_id}/{masked_webhook_token}"

# Logging des erreurs
except KeyError as e:
    logging.error(f"Variable d'environnement manquante : {e}")
    exit(1)
except ValueError:
    logging.error("REFRESH_TIME doit être un entier valide.")
    exit(1)

# Affichage des URLs et configurations
logging.info(f"GPU: {PRODUCT_NAME}")
logging.info(f"URL Webhook Discord: {wh_masked_url}")
logging.info(f"URL API SKU: {API_URL_SKU}")
logging.info(f"URL API Stock: {API_URL_STOCK}")
logging.info(f"URL produit: {PRODUCT_URL}")
logging.info(f"Temps d'actualisation: {REFRESH_TIME} secondes")
logging.info(f"Mode Test: {TEST_MODE}")


# Entêtes HTTP
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

# Session avec retries
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

# Stockage de l'état des stocks
global_stock_status = {}

# Stocke le dernier SKU connu
last_sku = None
first_run = True  # Before calling check_rtx_50_founders

# Notifications Discord
def send_discord_notification(gpu_name: str, product_link: str, products_price: str):
    
    # Récupérer le timestamp UNIX actuel
    timestamp_unix = int(time.time())

    if TEST_MODE:
        logging.info(f"[TEST MODE] Notification Discord: {gpu_name} disponible !")
        return
    
    embed = {
        "title": f"🚀 {PRODUCT_NAME} EN STOCK !",
        "color": 3066993,
        "thumbnail": {
            "url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/RTX5000.jpg"
        },
        "author": {
            "name": "Nvidia Founder Editions"
        },

        "fields": [
            {
            "name": "Prix",
            "value": f"`{products_price}€`",
            "inline": True
            },

            {
            "name": "Heure",
            "value": f"<t:{timestamp_unix}:d> <t:{timestamp_unix}:T>",
            "inline": True
            },
        ],
        "description": f"**:point_right: [Acheter maintenant]({product_link})**",
        "footer": {
            "text": "NviBot • JV Hardware 2.0",
            "icon_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg"
        }
    }
    payload = {"content": "@everyone", "username": "NviBot", "avatar_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg", "embeds": [embed]}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("✅ Notification envoyée sur Discord.")
        else:
            logging.error(f"❌ Erreur Webhook : {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"🚨 Erreur lors de l'envoi du webhook : {e}")

def send_out_of_stock_notification(gpu_name: str, product_link: str, products_price: str):
    
    # Récupérer le timestamp UNIX actuel
    timestamp_unix = int(time.time())

    if TEST_MODE:
        logging.info(f"[TEST MODE] Notification Discord: {gpu_name} hors stock !")
        return
    
    embed = {
        "title": f"❌ {PRODUCT_NAME} n'est plus en stock",
        "color": 15158332,  # Rouge pour hors stock
        "thumbnail": {
            "url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/RTX5000.jpg"
        },
        "url": f"{product_link}",
        "author": {
            "name": "Nvidia Founder Editions"
        },
        
        "footer": {
            "text": "NviBot • JV Hardware 2.0",
            "icon_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg"
        },

        "fields": [
            {
            "name": "Heure",
            "value": f"<t:{timestamp_unix}:d> <t:{timestamp_unix}:T>",
            "inline": True
            }
        ]
    }
    payload = {"username": "NviBot", "avatar_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg", "embeds": [embed]}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("✅ Notification 'hors stock' envoyée sur Discord.")
        else:
            logging.error(f"❌ Erreur Webhook : {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"🚨 Erreur lors de l'envoi du webhook : {e}")

def send_sku_change_notification(old_sku: str, new_sku: str, product_link: str):
    
    # Récupérer le timestamp UNIX actuel
    timestamp_unix = int(time.time())

    if TEST_MODE:
        logging.info(f"[TEST MODE] Changement de SKU détecté : {old_sku} → {new_sku}")
        return

    embed = {
        "title": f"🔄 {PRODUCT_NAME} Changement de SKU détecté",
        "url": f"{product_link}",
        "description": f"**Ancien SKU** : `{old_sku}`\n**Nouveau SKU** : `{new_sku}`",
        "color": 16776960,  # Jaune

        "footer": {
            "text": "NviBot • JV Hardware 2.0",
            "icon_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg"
        },

        "fields": [
            {
            "name": "Heure",
            "value": f"<t:{timestamp_unix}:d> <t:{timestamp_unix}:T>",
            "inline": True
            }
        ]
    }
    
    payload = {
        "content": "@everyone ⚠️ Potentiel drop imminent !",
        "username": "NviBot",
        "avatar_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/ds_wh_pp.jpg",
        "embeds": [embed]
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("✅ Notification de changement de SKU envoyée sur Discord.")
        else:
            logging.error(f"❌ Erreur Webhook : {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"🚨 Erreur lors de l'envoi du webhook : {e}")

# Recherche du stock
def check_rtx_50_founders():
    global global_stock_status, last_sku, first_run

    # Appel vers l'API produit pour récupérer le sku et l'upc

    try:
        response = session.get(API_URL_SKU, headers=HEADERS, timeout=10)
        logging.info(f"Réponse de l'API SKU : {response.status_code}")
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur API SKU : {e}")
        return

   # Recherche du produit dont le GPU correspond à PRODUCT_NAME
    product_details = None

    for p in data['searchedProducts']['productDetails']:
        gpu_name = p.get("gpu", "").strip()
        
        # Si le GPU correspond exactement à PRODUCT_NAME
        if gpu_name == PRODUCT_NAME.strip():
            product_details = p
            break  # Sortir dès qu'on trouve le bon produit

    if not product_details:
        logging.warning(f"⚠️ Aucun produit avec le GPU '{PRODUCT_NAME}' trouvé.")
        return

    # Récupérer le SKU pour le GPU trouvé
    product_sku = product_details['productSKU']
    product_upc = product_details.get('productUPC', "")


    # Vérifier si c'est la première exécution
    if last_sku is not None and product_sku != last_sku:
        if not first_run:  # Évite d'envoyer une notification au premier appel
            product_link = PRODUCT_URL
            logging.warning(f"⚠️ SKU modifié : {last_sku} → {product_sku}")
            send_sku_change_notification(last_sku, product_sku, product_link)

    # Mettre à jour le SKU stocké
    last_sku = product_sku
    first_run = False  # Désactive la protection après la première exécution

    if not isinstance(product_upc, list):
        product_upc = [product_upc]
    
    # Construction de l'url de l'API de stock et appel pour vérifier le statut
    API_URL = API_URL_STOCK + product_sku
    logging.info(f"URL de l'API de stock appelée : {API_URL}")
    
    try:
        response = session.get(API_URL, headers=HEADERS, timeout=10)
        logging.info(f"Réponse de l'API : {response.status_code}")  
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur API Stock : {e}")
        return

    products = data.get("listMap", [])
    products_price = 'Prix non disponible'  # Valeur par défaut

    # Vérification de la liste des produits et récupération du prix
    if isinstance(products, list) and len(products) > 0:
        for product in products:
            price = product.get("price", 'Prix non disponible')
            if price != 'Prix non disponible':
                products_price = price  # Utiliser le prix trouvé
                break  # Sortir dès qu'on trouve un prix
    else:
        logging.error("La liste des produits est vide ou mal formée.")

    found_in_stock = set()

    # Recherche du statut et notifications selon le statut
    for p in products:
        gpu_name = p.get("fe_sku", "").upper()
        is_active = p.get("is_active") == "true"
        if is_active and any(target.upper() in gpu_name for target in product_upc):
            found_in_stock.add(gpu_name)

    for gpu in product_upc:
        gpu_upper = gpu.upper()
        currently_in_stock = gpu_upper in found_in_stock
        previously_in_stock = global_stock_status.get(gpu_upper, False)
        
        if currently_in_stock and not previously_in_stock:
            product_link = PRODUCT_URL
            send_discord_notification(gpu_upper, product_link, products_price)
            global_stock_status[gpu_upper] = True
            logging.info(f"{gpu} est maintenant en stock!")
        elif not currently_in_stock and previously_in_stock:
            product_link = PRODUCT_URL
            send_out_of_stock_notification(gpu_upper, product_link, products_price)
            global_stock_status[gpu_upper] = False
            logging.info(f"{gpu} n'est plus en stock.")

        elif currently_in_stock and previously_in_stock:
            logging.info(f"{gpu} est actuellement en stock.")
            
        else:
            logging.info(f"{gpu} est actuellement hors stock.")

# Boucle
if __name__ == "__main__":
    while True:
        check_rtx_50_founders()
        time.sleep(REFRESH_TIME)
