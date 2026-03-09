import feedparser
import facebook
import os
from bs4 import BeautifulSoup

# --- CONFIGURATION DIRECTE ---
# Ton Token de Page (Garde-le bien dans les guillemets)
PAGE_TOKEN = "EAAMfBfPFbyMBQ8iQizXN7B3a9ZCPgOjvUHASnCZASUC4o5wRI8lv8pa2KtofzAMnHF9dXyhs08ZAXadgGIFiqtfnZC8Q9WgCvov3FnQRPO4Vg6TUEv3RzxwHZB1smdxECKm7TCl2a2iVCdrIzqZASZB2JzbGJo6OMU3pG6fZCm1tziwCziYNZBHYMmdxdZCYRnIePQ"

# Liens des flux RSS
RSS_ARDENNAIS = "https://www.lardennais.fr/rss/region/ardennes"
RSS_UNION = "https://www.lunion.fr/rss/direct"

# Fichier pour la mémoire (pour éviter les doublons)
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
    print("--- Vérification des actualités ---")
    last_link = obtenir_dernier_post()
    
    article_a_poster = None
    source_nom = ""

    # 1. TENTATIVE L'ARDENNAIS
    print("Lecture de l'Ardennais...")
    feed_a = feedparser.parse(RSS_ARDENNAIS)
    
    if len(feed_a.entries) > 0:
        premier_a = feed_a.entries[0]
        if premier_a.link != last_link:
            article_a_poster = premier_a
            source_nom = "L'Ardennais"
    
    # 2. TENTATIVE L'UNION (si rien de neuf sur l'Ardennais)
    if article_a_poster is None:
        print("Rien de neuf sur l'Ardennais, check de l'Union...")
        feed_u = feedparser.parse(RSS_UNION)
        if len(feed_u.entries) > 0:
            premier_u = feed_u.entries[0]
            if premier_u.link != last_link:
                article_a_poster = premier_u
                source_nom = "L'Union"

    # 3. SI RIEN DE NEUF DU TOUT
    if article_a_poster is None:
        print("Aucun nouvel article à publier pour le moment.")
        return

    # 4. PRÉPARATION DU POST
    titre = article_a_poster.title
    lien = article_a_poster.link
    
    # Nettoyage du texte (enlève le HTML)
    resume_raw = article_a_poster.summary if 'summary' in article_a_poster else ""
    resume_propre = BeautifulSoup(resume_raw, "html.parser").get_text()
    
    # On prend le début (300 caractères max)
    extrait = (resume_propre[:300] + '..') if len(resume_propre) > 300 else resume_propre

    message = (
        f"🔴 {source_nom} : {titre}\n\n"
        f"{extrait}\n\n"
        f"Lire la suite ici : {lien}\n\n"
        f"#actualiter"
    )

    # 5. ENVOI SUR FACEBOOK
    try:
        graph = facebook.GraphAPI(access_token=PAGE_TOKEN)
        # On met le lien dans le paramètre 'link' pour que l'image s'affiche
        graph.put_object(
            parent_object='me', 
            connection_name='feed', 
            message=message, 
            link=lien
        )
        sauvegarder_dernier_post(lien)
        print(f"✅ SUCCÈS : '{titre}' posté sur Facebook !")
    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    publier_actu()
    lien = article_a_poster.link
    
    # Nettoyage du résumé (summary) pour enlever les balises HTML
    resume_raw = article_a_poster.summary if 'summary' in article_a_poster else ""
    resume_propre = BeautifulSoup(resume_raw, "html.parser").get_text()
    
    # On limite le texte pour ne pas faire trop long (300 caractères)
    extrait = (resume_propre[:300] + '..') if len(resume_propre) > 300 else resume_propre

    message = (
        f"🔴 {source_nom} : {titre}\n\n"
        f"{extrait}\n\n"
        f"Lire la suite ici : {lien}\n\n"
        f"#actualiter"
    )

    # 5. PUBLICATION FACEBOOK
    try:
        graph = facebook.GraphAPI(access_token=PAGE_TOKEN)
        # En envoyant le paramètre 'link', Facebook génère l'image automatiquement
        graph.put_object(
            parent_object='me', 
            connection_name='feed', 
            message=message, 
            link=lien
        )
        sauvegarder_dernier_post(lien)
        print(f"✅ SUCCÈS : Article '{titre}' publié sur Facebook.")
    except Exception as e:
        print(f"❌ ERREUR Facebook : {e}")

if __name__ == "__main__":
    publier_actu()
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
  
