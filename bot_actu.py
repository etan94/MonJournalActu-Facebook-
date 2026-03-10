import feedparser
import facebook
import json
import os
import time
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; RSSBot/1.0)"}

USER_TOKEN = "EAAMfBfPFbyMBQzZBV6X38pbAZAIDEG0Gess9OAOgL14mykaOsvYlcSUkRZB0vIrJddeobax0cQqkscJ0W2iQmVKE8nPwuCGNHXMI3VB77m0VCJ18jt24tNvYFQ2lqViZAmJN9M5ijdNZBLORClwld8zZCrK4MmCXRNRDX4EuIofrxXOItwGx5oS3XozNHY"

SOURCES = [
    {
        "nom": "Ardennais",
        "url": "https://news.google.com/rss/search?q=ardennes&hl=fr&gl=FR&ceid=FR:fr",
        "prefixe": "[Ardennes]",
        "hashtags": "#Ardennes #Actualite #LArdennais",
    },
]

FENETRE_MINUTES = 1440
FICHIER_HISTORIQUE = "articles_postes.json"


def charger_historique():
    if not os.path.exists(FICHIER_HISTORIQUE):
        return set()
    try:
        with open(FICHIER_HISTORIQUE, "r") as f:
            data = json.load(f)
        return set(data.get("liens", []))
    except Exception:
        return set()


def sauvegarder_historique(liens):
    liste = list(liens)[-500:]
    with open(FICHIER_HISTORIQUE, "w") as f:
        json.dump({"liens": liste}, f, indent=2)


def resoudre_url(url):
    try:
        resp = requests.head(url, headers=HEADERS, allow_redirects=True, timeout=8)
        final = resp.url
        if "?" in final:
            base, params = final.split("?", 1)
            propres = [p for p in params.split("&") if not p.lower().startswith("utm_")]
            final = base + ("?" + "&".join(propres) if propres else "")
        return final
    except Exception:
        return url


def est_recent(entry):
    pub = entry.get("published_parsed") or entry.get("updated_parsed")
    if not pub:
        return True
    article_time = datetime.fromtimestamp(time.mktime(pub))
    return datetime.utcnow() - article_time <= timedelta(minutes=FENETRE_MINUTES)


def construire_message(entry, source, lien):
    titre = entry.get("title", "Sans titre")
    res_raw = entry.get("summary", "")
    res_txt = BeautifulSoup(res_raw, "html.parser").get_text().strip()
    extrait = (res_txt[:300] + "...") if len(res_txt) > 300 else res_txt
    lignes = [source["prefixe"] + " " + titre, ""]
    if extrait:
        lignes += [extrait, ""]
    lignes += ["Lien : " + lien, "", source["hashtags"]]
    return "\n".join(lignes)


def publier_actu():
    print("--- Verification RSS ---")

    graph = facebook.GraphAPI(access_token=USER_TOKEN)
    deja_postes = charger_historique()
    nouveaux_liens = set()
    total_postes = 0

    for source in SOURCES:
        print("Source : " + source["nom"])
        feed = feedparser.parse(source["url"])

        articles_valides = [
            e for e in feed.entries
            if e.get("link") and e["link"] not in deja_postes and est_recent(e)
        ]

        print(str(len(articles_valides)) + " article(s) a poster")

        articles_valides.sort(
            key=lambda e: time.mktime(
                e.get("published_parsed") or e.get("updated_parsed") or time.gmtime(0)
            )
        )

        for entry in articles_valides:
            lien_rss = entry["link"]
            lien = resoudre_url(lien_rss)
            msg = construire_message(entry, source, lien)
            try:
                graph.put_object(
                    parent_object="me",
                    connection_name="feed",
                    message=msg,
                    link=lien,
                )
                print("OK - " + entry.get("title", lien)[:60])
                nouveaux_liens.add(lien_rss)
                total_postes += 1
                time.sleep(2)
            except facebook.GraphAPIError as err:
                print("ERREUR Facebook : " + str(err))
            except Exception as err:
                print("ERREUR : " + str(err))

    if nouveaux_liens:
        sauvegarder_historique(deja_postes | nouveaux_liens)

    print("Termine - " + str(total_postes) + " article(s) publie(s)")


if __name__ == "__main__":
    publier_actu()
