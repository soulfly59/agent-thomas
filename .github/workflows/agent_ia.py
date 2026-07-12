import os
import time
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# ================= CONFIGURATION =================
# On remet ton vrai lien Discord officiel ici en direct !
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1525519939690041354/5IMMa21opgxhjcTSeT0vm8WsKmPk3vOoRULwUXGRcNgf4oK6sEey8h3AJzawlIprJKCa"
URL_IMMOWEB = "https://www.immoweb.be/fr/recherche/maison-et-appartement/a-louer?countries=BE&priceType=MONTHLY_RENTAL_PRICE&minPrice=800&maxPrice=1200&postalCodes=BE-7070&districts=SOIGNIES&page=1&orderBy=relevance"
# =================================================

def envoyer_discord(titre, prix, localite, lien_bien):
    texte_message = (
        f"🏠 **[Agent Thomas] Nouveau bien trouvé sur Immoweb !**\n"
        f"🏷️ **Type :** {titre}\n"
        f"📍 **Région :** {localite}\n"
        f"💰 **Loyer :** {prix}\n"
        f"🌐 **Lien de l'annonce :** {lien_bien}"
    )
    data = {"username": "Agent Thomas", "content": texte_message}
    requests.post(DISCORD_WEBHOOK_URL, json=data)

def surveiller_immoweb():
    print("🕵️‍♂️ Thomas scanne la zone de Soignies / Le Rœulx...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="fr-BE"
        )
        page = context.new_page()
        try:
            page.goto(URL_IMMOWEB, wait_until="domcontentloaded")
            time.sleep(6)
            html = page.content()
            browser.close()
        except Exception as e:
            print(f"❌ Erreur Immoweb : {e}")
            browser.close()
            return

    soup = BeautifulSoup(html, 'html.parser')
    
    articles = soup.find_all('li', class_='search-results__item')
    if not articles:
        articles = soup.find_all('article', class_='iw-card--property')
    if not articles:
        articles = [a for a in soup.find_all('a') if a.get('href') and '/fr/annonce/' in a.get('href')]

    if not articles:
        print("❌ Impossible de lire les blocs de résultats.")
        return

    premier_bien = articles[0]
    try:
        lien = premier_bien.get('href') if premier_bien.name == 'a' else (premier_bien.find('a').get('href') if premier_bien.find('a') else None)
        if not lien: return
        if lien.startswith('/'): lien = f"https://www.immoweb.be{lien}"

        texte_complet = " ".join(premier_bien.get_text(separator=" ").split())
        titre = "🏢 Appartement à louer" if "Appartement" in texte_complet else "🏠 Maison à louer" if "Maison" in texte_complet else "Logement trouvé"
        
        prix = "Prix non spécifié"
        mots = texte_complet.split()
        for i, mot in enumerate(mots):
            if "€" in mot:
                if i > 0 and mots[i-1].replace('(','').replace('+','').replace('.','').isdigit():
                    prix = f"{mots[i-1]} €"
                    break
                prix = mot

        print(f"🆕 Bien détecté ! Envoi à Discord...")
        envoyer_discord(titre, prix, "Soignies / Le Rœulx", lien)

    except Exception as e:
        print(f"❌ Erreur analyse du premier bien : {e}")

if __name__ == "__main__":
    surveiller_immoweb()
