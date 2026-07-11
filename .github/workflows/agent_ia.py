import os
import time
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# ================= CONFIGURATION =================
# C'est cette ligne magique qui va aller chercher ton lien secret en cachette :
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

# URL Immoweb filtrée uniquement sur : Soignies (Arrondissement) et Le Rœulx (7070) | 800€ - 1200€
URL_IMMOWEB = "https://www.immoweb.be/fr/recherche/maison-et-appartement/a-louer?countries=BE&priceType=MONTHLY_RENTAL_PRICE&minPrice=800&maxPrice=1200&postalCodes=BE-7070&districts=SOIGNIES&page=1&orderBy=relevance"
FICHIER_MEMOIRE = "derniers_biens_immo.txt"
# =================================================

def envoyer_discord(titre, prix, localite, lien_bien):
    """L'Agent Thomas envoie le logement trouvé sur ton Discord"""
    texte_message = (
        f"🏠 **[Agent Thomas] Nouveau bien trouvé sur Immoweb !**\n"
        f"🏷️ **Type :** {titre}\n"
        f"📍 **Région :** {localite}\n"
        f"💰 **Loyer :** {prix}\n"
        f"🌐 **Lien de l'annonce :** {lien_bien}"
    )
    
    data = {
        "username": "Agent Thomas",
        "content": texte_message
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        if response.status_code in [200, 204]:
            print("🚀 Notification Immoweb envoyée sur Discord avec succès !")
        else:
            print(f"⚠️ Discord a répondu avec le code : {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi Discord : {e}")

def charger_anciens_biens():
    if not os.path.exists(FICHIER_MEMOIRE):
        return set()
    with open(FICHIER_MEMOIRE, "r") as f:
        return set(f.read().splitlines())

def sauvegarder_nouveau_lien(lien):
    with open(FICHIAM_MEMOIRE, "a") as f:
        f.write(lien + "\n")

def surveiller_immoweb():
    print("🕵️‍♂️ Thomas lance les recherches sur Soignies et Le Rœulx uniquement...")
    biens_connus = charger_anciens_biens()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="fr-BE"
        )
        page = context.new_page()
        
        try:
            print("🌐 Connexion à Immoweb...")
            page.goto(URL_IMMOWEB, wait_until="domcontentloaded")
            time.sleep(6)
            html = page.content()
            browser.close()
        except Exception as e:
            print(f"❌ Erreur de connexion à Immoweb : {e}")
            browser.close()
            return

    soup = BeautifulSoup(html, 'html.parser')
    
    # Extraction des éléments de la page
    articles = soup.find_all('li', class_='search-results__item')
    if not articles:
        articles = soup.find_all('article', class_='iw-card--property')
    if not articles:
        articles = [a for a in soup.find_all('a') if a.get('href') and '/fr/annonce/' in a.get('href')]

    if not articles:
        print("❌ Immoweb bloque l'affichage ou aucun bien trouvé.")
        return

    print(f"📊 {len(articles)} éléments détectés. Analyse du bien le plus récent...")

    premier_bien = articles[0]
    try:
        if premier_bien.name == 'a':
            lien = premier_bien.get('href')
        else:
            lien_elem = premier_bien.find('a')
            lien = lien_elem.get('href') if lien_elem else None

        if not lien:
            print("❌ Impossible de récupérer le lien.")
            return

        if lien.startswith('/'):
            lien = f"https://www.immoweb.be{lien}"

        texte_complet = premier_bien.get_text(separator=" ").strip()
        texte_nettoye = " ".join(texte_complet.split())
        
        titre = "Logement trouvé (cliquez sur le lien)"
        if "Appartement" in texte_nettoye: titre = "🏢 Appartement à louer"
        elif "Maison" in texte_nettoye: titre = "🏠 Maison à louer"
        
        prix = "Entre 800€ et 1200€"
        for mot in texte_nettoye.split():
            if "€" in mot and mot != "€":
                prix = mot
                break

        print(f"🔎 En ligne actuellement : {titre} - {prix}")

        if lien not in biens_connus:
            print("🆕 Nouveau logement détecté ! Thomas transmet à Discord...")
            envoyer_discord(titre, prix, "Soignies / Le Rœulx", lien)
            sauvegarder_nouveau_lien(lien)
        else:
            print("😴 Déjà en mémoire. Pas de doublon envoyé.")

    except Exception as e:
        print(f"❌ Erreur lors de l'analyse du bien : {e}")

if __name__ == "__main__":
    surveiller_immoweb()
