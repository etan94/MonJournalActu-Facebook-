import feedparser
import facebook
import os
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
PAGE_TOKEN = "EAAMfBfPFbyMBQ8iQizXN7B3a9ZCPgOjvUHASnCZASUC4o5wRI8lv8pa2KtofzAMnHF9dXyhs08ZAXadgGIFiqtfnZC8Q9WgCvov3FnQRPO4Vg6TUEv3RzxwHZB1smdxECKm7TCl2a2iVCdrIzqZASZB2JzbGJo6OMU3pG6fZCm1tziwCziYNZBHYMmdxdZCYRnIePQ"

RSS_ARDENNAIS = "https://www.lardennais.fr/rss/region/ardennes"
RSS_UNION = "https://www.lunion.fr/rss/direct"

def publier_actu():
    print("--- Vérification des actualités ---")
    
    article_a_poster = None
    source_nom = ""

    # 1. TEST ARDENNAIS
    print("Lecture de l'Ardennais...")
    feed_a = feedparser.parse(RSS_ARDENNAIS)
    if len(feed_a.entries) > 0:
        article_a_poster = feed_a.entries[0]
        source_nom = "L'Ardennais"
    else:
        # 2. TEST UNION (si l'Ardennais ne répond pas)
        print("Check de l'Union...")
        feed_u = feedparser.parse(RSS_UNION)
        if len(feed_u.entries) > 0:
            article_a_poster = feed_u.entries[0]
            source_nom = "L'Union"

    # --- ÉTAPE CRUCIALE : ARRÊT SI RIEN ---
    if article_a_poster is None:
        print("Aucun article trouvé sur les flux. Arrêt du script.")
        return # ICI le script s'arrête proprement

    # 3. VÉRIFICATION DE L'HEURE (DOUBLONS)
    pub_date = article_a_poster.get('published_parsed') or article_a_poster.get('updated_parsed')
    if pub_date:
        article_time = datetime.fromtimestamp(time.mktime(pub_date))
        now = datetime.utcnow()
        # Si l'article a plus de 65 minutes, on ne poste pas
        if now - article_time > timedelta(minutes=65):
            print(f"L'article date de {article_time}. Trop vieux, déjà posté.")
            return

    # 4. PRÉPARATION DU POST (Seulement si on a un article récent)
    titre = article_a_poster.title
    lien = article_a_poster.link
    resume_raw = article_a_poster.summary if 'summary' in article_a_poster else ""
    resume_propre = BeautifulSoup(resume_raw, "html.parser").get_text()
    extrait = (resume_propre[:300] + '..') if len(resume_propre) > 300 else resume_propre

    message = f"🔴 {source_nom} : {titre}\n\n{extrait}\n\nLire la suite ici : {lien}\n\n#actualiter"

    # 5. ENVOI
    try:
        graph = facebook.GraphAPI(access_token=PAGE_TOKEN)
        graph.put_object(parent_object='me', connection_name='feed', message=message, link=lien)
        print(f"✅ Posté avec succès : {titre}")
    except Exception as e:
        print(f"❌ Erreur Facebook : {e}")

if __name__ == "__main__":
    publier_actu()
    except Exception as e:
        print(f"❌ Erreur Facebook : {e}")

if __name__ == "__main__":
    publier_actu()
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
  
