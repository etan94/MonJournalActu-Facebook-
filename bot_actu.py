import feedparser
import facebook
import os
import time

# --- CONFIGURATION ---
APP_ID = "878535355232035"
APP_SECRET = "0a456acba55d95d3932b7a5ae0037915"
# Remplace par ton TOKEN DE PAGE (généré dans l'Explorer Graph API)
PAGE_TOKEN = "TON_TOKEN_DE_PAGE_ICI"

# Liens des flux RSS
RSS_ARDENNAIS = "https://www.lardennais.fr/rss/region/ardennes"
RSS_UNION = "https://www.lunion.fr/rss/direct"

# Fichier pour ne pas poster deux fois le même article
LOG_FILE = "dernier_article.txt"

def obtenir_dernier_post():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return f.read().strip()
    return ""

def sauvegarder_dernier_post(lien):
    with open(LOG_FILE, "w") as f:
        f.write(lien)

def publier_actu():
    print("Vérification des actualités...")
    last_link = obtenir_dernier_post()
    
    # 1. On check l'Ardennais
    feed = feedparser.parse(RSS_ARDENNAIS)
    article = feed.entries[0]
    source_name = "L'Ardennais"

    # 2. Si c'est le même que le dernier, on check l'Union
    if article.link == last_link:
        print("Rien de neuf sur l'Ardennais, check de l'Union...")
        feed = feedparser.parse(RSS_UNION)
        article = feed.entries[0]
        source_name = "L'Union"

    # 3. Si toujours rien de neuf, on s'arrête
    if article.link == last_link:
        print("Aucun nouvel article trouvé.")
        return

    # 4. Préparation du message
    # On prend le résumé (summary) et on coupe si c'est trop long
    texte_debut = article.summary if 'summary' in article else ""
    # Nettoyage rapide des balises HTML si présentes
    from bse4 import BeautifulSoup
    texte_propre = BeautifulSoup(texte_debut, "html.parser").get_text()

    message = (
        f"🔴 ACTU ({source_name}) : {article.title}\n\n"
        f"{texte_propre[:300]}...\n\n"
        f"Lire la suite ici : {article.link}\n\n"
        f"#actualiter"
    )

    # 5. Envoi à Facebook
    try:
        graph = facebook.GraphAPI(access_token=PAGE_TOKEN)
        # On passe le lien dans 'link' pour que Facebook génère l'image tout seul
        graph.put_object(
            parent_object='me', 
            connection_name='feed', 
            message=message, 
            link=article.link
        )
        sauvegarder_dernier_post(article.link)
        print(f"✅ Posté avec succès : {article.title}")
    except Exception as e:
        print(f"❌ Erreur Facebook : {e}")

# Lancement automatique toutes les heures (3600 secondes)
if __name__ == "__main__":
    while True:
        publier_actu()
        print("En attente pendant 1 heure...")
        time.sleep(3600)
  
