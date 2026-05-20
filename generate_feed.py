import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bs4 import BeautifulSoup
from datetime import datetime, UTC

import os
import re
import time

URL = "https://www.aziendaspecialecarlentini.it/"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

# blacklist minima SOLO sezioni statiche
blacklist = [
    "privacy",
    "modulistica",
    "problema",
    "informativa"
]

# =========================
# SESSIONE ROBUSTA
# =========================

session = requests.Session()

retry_strategy = Retry(
    total=5,
    connect=5,
    read=5,
    backoff_factor=2,
    status_forcelist=[
        429,
        500,
        502,
        503,
        504
    ],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(
    max_retries=retry_strategy
)

session.mount("https://", adapter)
session.mount("http://", adapter)

# =========================
# FUNZIONE RICHIESTA SICURA
# =========================

def safe_get(url):

    for tentativo in range(3):

        try:

            response = session.get(
                url,
                headers=headers,
                timeout=(20, 60)
            )

            response.raise_for_status()

            return response

        except Exception as e:

            print(
                f"ERRORE RETE "
                f"(tentativo {tentativo + 1}/3): {e}"
            )

            if tentativo < 2:

                pausa = 5 * (tentativo + 1)

                print(
                    f"Attendo {pausa} secondi..."
                )

                time.sleep(pausa)

            else:

                raise

# =========================
# HOMEPAGE
# =========================

print("Scarico homepage Azienda Speciale...")

response = safe_get(URL)

print("Homepage scaricata")

soup = BeautifulSoup(
    response.text,
    "html.parser"
)

links = soup.find_all("a", href=True)

items = []
usati = set()

articoli_validi = []

# =========================
# RACCOLTA ARTICOLI
# =========================

for link in links:

    href = link.get("href", "")

    titolo = link.get_text(strip=True)

    titolo = (
        titolo
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace("â€“", "-")
        .replace("â€”", "-")
        .replace("â", "-")
    )

    if not titolo:
        continue

    if len(titolo) < 10:
        continue

    titolo_lower = titolo.lower()

    if any(b in titolo_lower for b in blacklist):
        continue

    match_data = re.search(
        r"/(\d{4})/(\d{2})/(\d{2})/",
        href
    )

    if not match_data:
        continue

    if href in usati:
        continue

    usati.add(href)

    articoli_validi.append({
        "href": href,
        "titolo": titolo
    })

# tieni solo i primi 20 articoli
# la homepage è già quasi ordinata
articoli_validi = articoli_validi[:20]

print(
    f"Trovati "
    f"{len(articoli_validi)} "
    f"articoli validi"
)

# =========================
# ANALISI ARTICOLI
# =========================

for articolo in articoli_validi:

    href = articolo["href"]

    titolo = articolo["titolo"]

    print(f"ARTICOLO: {titolo}")

    try:

        # piccola pausa anti-rate-limit
        time.sleep(1)

        articolo_response = safe_get(href)

        articolo_soup = BeautifulSoup(
            articolo_response.text,
            "html.parser"
        )

        match_data = re.search(
            r"/(\d{4})/(\d{2})/(\d{2})/",
            href
        )

        anno = int(match_data.group(1))
        mese = int(match_data.group(2))
        giorno = int(match_data.group(3))

        pub_date = datetime(
            anno,
            mese,
            giorno,
            tzinfo=UTC
        )

        print(
            f"DATA TROVATA: "
            f"{giorno}/{mese}/{anno}"
        )

        descrizione = titolo

        paragrafi = articolo_soup.find_all("p")

        for p in paragrafi:

            testo = p.get_text(strip=True)

            if len(testo) > 80:

                descrizione = testo[:500]
                break

        items.append({
            "title": titolo,
            "link": href,
            "description": descrizione,
            "pubDate": pub_date
        })

    except Exception as e:

        print(
            f"ERRORE ARTICOLO "
            f"{titolo}: {e}"
        )

# =========================
# ORDINE FINALE
# =========================

items.sort(
    key=lambda x: x["pubDate"],
    reverse=True
)

# tieni solo le ultime 15
items = items[:15]

print("\n========== ORDINE FINALE ==========\n")

for item in items:

    print(
        item["pubDate"].strftime("%d/%m/%Y"),
        "-",
        item["title"]
    )

print("\n===================================\n")

# =========================
# GENERAZIONE RSS
# =========================

rss_items = ""

for item in items:

    pub_date_str = item["pubDate"].strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )

    rss_items += f"""
    <item>
        <title><![CDATA[{item['title']}]]></title>
        <link>{item['link']}</link>
        <description><![CDATA[{item['description']}]]></description>
        <pubDate>{pub_date_str}</pubDate>
        <guid>{item['link']}</guid>
    </item>
    """

rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>

    <title>Azienda Speciale Carlentini</title>

    <link>{URL}</link>

    <description>
        Feed RSS automatico Azienda Speciale Carlentini
    </description>

    <lastBuildDate>
        {datetime.now(UTC).strftime('%a, %d %b %Y %H:%M:%S GMT')}
    </lastBuildDate>

    {rss_items}

</channel>
</rss>
"""

output_file = os.path.abspath("feed.xml")

with open(
    output_file,
    "w",
    encoding="utf-8"
) as f:

    f.write(rss_content)

print(
    f"Feed creato con "
    f"{len(items)} elementi"
)

print(
    f"Feed salvato in: "
    f"{output_file}"
)