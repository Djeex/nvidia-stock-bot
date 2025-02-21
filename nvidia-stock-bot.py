import requests
import logging
import time
import os
from requests.adapters import HTTPAdapter, Retry

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logging.info("Démarrage du script")

# Récupération des variables d'environnement
try:
    DISCORD_WEBHOOK_URL = os.environ['DISCORD_WEBHOOK_URL']
    API_URL_SKU = os.environ['API_URL_SKU']
    API_URL_STOCK = os.environ['API_URL_STOCK']
    REFRESH_TIME = int(os.environ['REFRESH_TIME'])  # Convertir en entier
    TEST_MODE = os.environ.get('TEST_MODE', 'False').lower() == 'true'
except KeyError as e:
    logging.error(f"Variable d'environnement manquante : {e}")
    exit(1)
except ValueError:
    logging.error("REFRESH_TIME doit être un entier valide.")
    exit(1)

# Affichage des URLs et configurations
logging.info(f"URL Webhook Discord: {DISCORD_WEBHOOK_URL[:30]}******")
logging.info(f"URL API SKU: {API_URL_SKU}")
logging.info(f"URL API Stock: {API_URL_STOCK}")
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

# Notifications Discord
def send_discord_notification(gpu_name: str, product_link: str, products_price: str):
    if TEST_MODE:
        logging.info(f"[TEST MODE] Notification Discord: {gpu_name} disponible !")
        return
    
    embed = {
        "title": f"🚀 {gpu_name} EN STOCK !",
        "color": 3066993,
        "thumbnail": {
            "url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/RTX5000.jpg"
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "author": {
            "name": "Nvidia Founder Editions"
        },

        "fields": [
            {
            "name": "Prix",
            "value": f"`{products_price} €`",
            "inline": True
            }
        ],
        "description": "**:point_right: [Acheter maintenant](https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&page=1&limit=12&gpu=RTX%205090,RTX%205080)**",
        "footer": {
            "text": "Par KevOut & Djeex"
        }
    }
    payload = {"content": "@everyone", "username": "NviBot", "avatar_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/RTX5000_pp.jpg", "embeds": [embed]}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("✅ Notification envoyée sur Discord.")
        else:
            logging.error(f"❌ Erreur Webhook : {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"🚨 Erreur lors de l'envoi du webhook : {e}")

def send_out_of_stock_notification(gpu_name: str, product_link: str, products_price: str):
    if TEST_MODE:
        logging.info(f"[TEST MODE] Notification Discord: {gpu_name} hors stock !")
        return
    
    embed = {
        "title": f"❌ {gpu_name} n'est plus en stock",
        "description": f":disappointed_relieved:",
        "color": 15158332,  # Rouge pour hors stock
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "thumbnail": {
            "url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/RTX5000.jpg"
        },
        "url": "https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&page=1&limit=12&gpu=RTX%205090,RTX%205080",
        "author": {
            "name": "Nvidia Founder Editions"
        },
        "footer": {
            "text": "Par KevOut & Djeex"
        }
    }
    payload = {"username": "NviBot", "avatar_url": "https://git.djeex.fr/Djeex/nvidia-stock-bot/raw/branch/main/assets/img/RTX5000_pp.jpg", "embeds": [embed]}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("✅ Notification 'hors stock' envoyée sur Discord.")
        else:
            logging.error(f"❌ Erreur Webhook : {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"🚨 Erreur lors de l'envoi du webhook : {e}")

# Recherche du stock
def check_rtx_50_founders():
    global global_stock_status

    # Appel vers l'API produit pour récupérer le sku et l'upc
    try:
        response = session.get(API_URL_SKU, headers=HEADERS, timeout=10)
        logging.info(f"Réponse de l'API : {response.status_code}")
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur API SKU : {e}")
        return

    product_details = data['searchedProducts']['productDetails'][0]
    product_sku = product_details['productSKU']
    product_upc = product_details.get('productUPC', "")
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
            product_link = "https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&page=1&limit=12&gpu=RTX%205090,RTX%205080"
            send_discord_notification(gpu_upper, product_link, products_price)
            global_stock_status[gpu_upper] = True
            logging.info(f"{gpu} est maintenant en stock!")
        elif not currently_in_stock and previously_in_stock:
            product_link = "https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&page=1&limit=12&gpu=RTX%205090,RTX%205080"
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
