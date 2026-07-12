import os
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# ================= CONFIGURATION =================
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
URL_IMMOWEB = "https://www.immoweb.be/fr/recherche/maison-et-appartement/a-louer?countries=BE&priceType=MONTHLY_RENTAL_PRICE&minPrice=800&maxPrice=1200&postalCodes=BE-7070&districts=SOIGNIES&page=1&orderBy=relevance"
MEMOIRE_FICHIER = "derniers_biens_immo.txt"
# =================================================

def envoyer_discord(titre, prix, localite, lien_bien):
    texte_message = (
        f"🏠 **[Agent Thomas] Nouveau bien trouvé sur Immoweb !**\n"
        f"🏷️ **Type :** {titre}\n"
        f"📍 **Région :** {localite}\n"
        f"💰 **Loyer :** {prix}\n"
        f"🌐 **Lien :** {lien_bien}"
    )
    data = {"username": "Agent Thomas", "content": texte_message}
    requests.post(DISCORD_WEBHOOK_URL, json=data)

def surveiller_immoweb():
    # 1. Lire la mémoire
    dernier_id = ""
    if os.path.exists(MEMOIRE_FICHIER):
        with open(MEMOIRE_FICHIER, "r") as f:
            dernier_id = f.read().strip()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL_IMMOWEB)
        page.wait_for_timeout(5000)
        soup = BeautifulSoup(page.content(), 'html.parser')
        browser.close()

    # Trouver l'annonce (le premier résultat)
    article = soup.find('article', class_='card--result')
    if not article:
        return

    lien = article.find('a', class_='card__title-link')['href']
    id_annonce = lien.split('/')[-1]

    # 2. Vérifier si c'est nouveau
    if id_annonce == dernier_id:
        print("😴 Pas de nouvelle annonce, on ne fait rien.")
        return

    # 3. Récupérer les infos et envoyer
    prix = article.find('p', class_='card--result__price').get_text(strip=True)
    titre = article.find('h2', class_='card__title').get_text(strip=True)
    
    envoyer_discord(titre, prix, "Soignies / Le Rœulx", lien)

    # 4. Sauvegarder l'id pour ne plus renvoyer cette annonce
    with open(MEMOIRE_FICHIER, "w") as f:
        f.write(id_annonce)

if __name__ == "__main__":
    surveiller_immoweb()
