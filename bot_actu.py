import feedparser
import facebook
import json
import os
import time
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; RSSBot/1.0)"
}

# --- CONFIGURATION ---
PAGE_TOKEN = "EAAMfBfPFbyMBQ8iQizXN7B3a9ZCPgOjvUHASnCZASUC4o5wRI8lv8pa2KtofzAMnHF9dXyhs08ZAXadgGIFiqtfnZC8Q9WgCvov3FnQRPO4Vg6TUEv3RzxwHZB1smdxECKm7TCl2a2iVCdrIzqZASZB2JzbGJo6OMU3pG6fZCm1tziwCziYNZBHYMmdxdZCYRnIePQ"

SOURCES = [
    {
        "nom": "L'Ardennais",
        "url": "https://news.google.com/rss/search?q=ardennes&hl=fr&gl=FR&ceid=FR:fr",
        "emoji": "🔴",
        "hashtags": "#Ardennes #Actualité #LArdennais",
    },
]

# Durée max d'un article (en minutes) pour être posté
FENETRE_MINUTES = 65

# Fichier pour mémoriser les articles déjà postés
FICHIER_HISTORIQUE = "articles_postes.json"


# --- GESTION DE L'HISTORIQUE ---

def charger_historique() -> set:
    """Charge les liens déjà postés depuis le fichier JSON."""
    if not os.path.exists(FICHIER_HISTORIQUE):
        return set()
    try:
        with open(FICHIER_HISTORIQUE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("liens", []))
    except (json.JSONDecodeError, KeyError):
        return set()


def sauvegarder_historique(liens: set):
    """Sauvegarde les liens postés dans le fichier JSON.
    On ne garde que les 500 derniers pour éviter un fichier trop lourd."""
    liste = list(liens)[-500:]
    with open(FICHIER_HISTORIQUE, "w", encoding="utf-8") as f:
        json.dump({"liens": liste, "maj": datetime.utcnow().isoformat()}, f, ensure_ascii=False, indent=2)


# --- RÉSOLUTION D'URL ---

def resoudre_url(url: str) -> str:
    """Suit les redirections pour obtenir l'URL finale de l'article.
    Si la requête échoue, renvoie l'URL d'origine."""
    try:
        resp = requests.head(url, headers=HEADERS, allow_redirects=True, timeout=8)
        final = resp.url
        # Nettoie les paramètres de tracking utm_*
        if "?" in final:
            base, params = final.split("?", 1)
            propres = [p for p in params.split("&") if not p.lower().startswith("utm_")]
            final = base + ("?" + "&".join(propres) if propres else "")
        print(f"    🔗 URL résolue : {final}")
        return final
    except Exception as e:
        print(f"    ⚠️  Impossible de résoudre l'URL ({e}), URL brute conservée.")
        return url


# --- TRAITEMENT D'UN ARTICLE ---

def est_recent(entry) -> bool:
    """Renvoie True si l'article a été publié dans la fenêtre de temps."""
    pub = entry.get("published_parsed") or entry.get("updated_parsed")
    if not pub:
        # Pas de date → on accepte par défaut
        return True
    article_time = datetime.fromtimestamp(time.mktime(pub))
    return datetime.utcnow() - article_time <= timedelta(minutes=FENETRE_MINUTES)


def construire_message(entry, source: dict, lien: str) -> str:
    """Construit le texte du post Facebook à partir d'un article RSS."""
    titre = entry.get("title", "(Sans titre)")
    res_raw = entry.get("summary", "")
    res_txt = BeautifulSoup(res_raw, "html.parser").get_text().strip()
    extrait = (res_txt[:300] + "…") if len(res_txt) > 300 else res_txt

    lignes = [
        f"{source['emoji']} {source['nom']} : {titre}",
        "",
    ]
    if extrait:
        lignes += [extrait, ""]
    lignes += [f"🔗 {lien}", "", source["hashtags"]]

    return "\n".join(lignes)


# --- BOUCLE PRINCIPALE ---

def publier_actu():
    print(f"\n{'='*50}")
    print(f"  Vérification RSS — {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*50}")

    deja_postes = charger_historique()
    graph = facebook.GraphAPI(access_token=PAGE_TOKEN)
    nouveaux_liens = set()
    total_postes = 0

    for source in SOURCES:
        print(f"\n[{source['nom']}] Lecture du flux : {source['url']}")
        feed = feedparser.parse(source["url"])

        if feed.bozo:
            print(f"  ⚠️  Erreur de parsing : {feed.bozo_exception}")

        articles_valides = [
            e for e in feed.entries
            if e.get("link") and e["link"] not in deja_postes and est_recent(e)
        ]

        print(f"  → {len(feed.entries)} article(s) trouvé(s), {len(articles_valides)} nouveau(x) récent(s)")

        # On publie du plus ancien au plus récent pour respecter l'ordre chronologique
        articles_valides.sort(
            key=lambda e: time.mktime(e.get("published_parsed") or e.get("updated_parsed") or time.gmtime(0))
        )

        for entry in articles_valides:
            lien_rss = entry["link"]
            print(f"\n  📰 {entry.get('title', lien_rss)[:80]}")
            lien = resoudre_url(lien_rss)
            msg = construire_message(entry, source, lien)
            try:
                graph.put_object(
                    parent_object="me",
                    connection_name="feed",
                    message=msg,
                    link=lien,
                )
                print(f"  ✅ Posté !")
                # On sauvegarde le lien RSS original pour l'historique
                nouveaux_liens.add(lien_rss)
                total_postes += 1
                # Petite pause pour éviter le rate-limiting Facebook
                time.sleep(2)
            except facebook.GraphAPIError as e:
                print(f"  ❌ Erreur Facebook : {e}")
            except Exception as e:
                print(f"  ❌ Erreur inattendue : {e}")

    # Mise à jour de l'historique
    if nouveaux_liens:
        sauvegarder_historique(deja_postes | nouveaux_liens)

    print(f"\n{'='*50}")
    print(f"  Terminé — {total_postes} article(s) publié(s)")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    publier_actu()        article_time = datetime.fromtimestamp(time.mktime(pub_date))
        if datetime.utcnow() - article_time > timedelta(minutes=65):
            print("Trop vieux.")
            return

    # 4. PREPA MESSAGE
    titre = article_a_poster.title
    lien = article_a_poster.link
    res_raw = article_a_poster.summary if 'summary' in article_a_poster else ""
    res_txt = BeautifulSoup(res_raw, "html.parser").get_text()
    extrait = (res_txt[:300] + '..') if len(res_txt) > 300 else res_txt
    msg = f"🔴 {source_nom} : {titre}\n\n{extrait}\n\nLien : {lien}\n\n#actualiter"

    # 5. ENVOI
    try:
        graph = facebook.GraphAPI(access_token=PAGE_TOKEN)
        graph.put_object(parent_object='me', connection_name='feed', message=msg, link=lien)
        print("Succes !")
    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    publier_actu()
