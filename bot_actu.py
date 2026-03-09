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
    print("--- Verif Actu ---")
    article_a_poster = None
    source_nom = ""

    # 1. TEST ARDENNAIS
    feed_a = feedparser.parse(RSS_ARDENNAIS)
    if len(feed_a.entries) > 0:
        article_a_poster = feed_a.entries[0]
        source_nom = "L'Ardennais"
    else:
        # 2. TEST UNION
        feed_u = feedparser.parse(RSS_UNION)
        if len(feed_u.entries) > 0:
            article_a_poster = feed_u.entries[0]
            source_nom = "L'Union"

    if article_a_poster is None:
        print("Rien trouve.")
        return

    # 3. VERIF DATE
    pub_date = article_a_poster.get('published_parsed') or article_a_poster.get('updated_parsed')
    if pub_date:
        article_time = datetime.fromtimestamp(time.mktime(pub_date))
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
