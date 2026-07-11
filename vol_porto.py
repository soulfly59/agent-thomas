import os
import time
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# ================= CONFIGURATION =================
DISCORD_WEBHOOK_URL = os.environ["https://discord.com/api/webhooks/1525519939690041354/5IMMa21opgxhjcTseT0vm8wSkmPk3vOoRULwUXGRCngf4oK6sEeY8h3AJzaWlIprJKCa"]

# Ton vrai lien officiel Google Flights :
URL_VOL = "https://www.google.com/travel/flights/search?tfs=CBwQAhojEgoyMDI2LTEwLTMwagcIARIDQ1JMcgwIAxIIL20vMHBtbjcaIxIKMjAyNi0xMS0wMWoMCAMSCC9tLzBwbW43cgcIARIDQ1JMQAFIAXABggELCP___________wGYAQE&hl=fr&gl=FR" 
PRIX_MAX = 130
# =================================================

def envoyer_discord(prix):
    texte_message = (
        f"✈️ **[Agent Thomas - Alerte Vol] Baisse de prix détectée !**\n"
        f"🇵🇹 **Vol :** Bruxelles Charleroi ➡️ Porto (30 oct - 1er nov)\n"
        f"💰 **Prix actuel :** {prix} € (Objectif : moins de {PRIX_MAX} €)\n"
        f"🎟️ **Lien pour réserver vite :** {URL_VOL}"
    )
    data = {"username": "Thomas Chasseur de Vols", "content": text_message}
    requests.post(DISCORD_WEBHOOK_URL, json=data)

def surveiller_vol():
    print("🕵️‍♂️ Thomas regarde le prix du vol vers Porto...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="fr-BE"
        )
        page = context.new_page()
        
        try:
            page.goto(URL_VOL, wait_until="networkidle")
            time.sleep(7) # On laisse le temps aux graphiques Google de s'afficher
            html = page.content()
            browser.close()
        except Exception as e:
            print(f"❌ Erreur Google Flights : {e}")
            browser.close()
            return

    soup = BeautifulSoup(html, 'html.parser')
    
    # Recherche du prix principal sur la page
    prix_elem = soup.find(string=lambda text: text and "€" in text)
    
    if prix_elem:
        texte_prix = "".join([c for c in prix_elem if c.isdigit()])
        if texte_prix:
            prix_actuel = int(texte_prix)
            print(f"🔎 Prix trouvé par Thomas : {prix_actuel} €")
            
            if prix_actuel <= PRIX_MAX:
                print("🎯 Prix cible atteint ! Envoi de l'alerte...")
                envoyer_discord(prix_actuel)
            else:
                print(f"😴 Toujours trop cher ({prix_actuel} €). On attend.")
        else:
            print("❌ Impossible de découper le prix.")
    else:
        print("❌ Aucun prix détecté sur la page.")

if __name__ == "__main__":
    surveiller_vol()
