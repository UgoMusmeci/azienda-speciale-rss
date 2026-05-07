import requests
from bs4 import BeautifulSoup
from datetime import datetime, UTC
import os
import re

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

print("Scarico homepage Azienda Speciale...")

response = requests.get(
    URL,
    headers=headers,
    timeout=30
)

response.raise_for_status()

print("Homepage scaricata")

soup = BeautifulSoup(
    response.text,
    "html.parser"
)

links = soup.find_all("a", href=True)

items = []
usati = set()

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
    )

    if not titolo:
        continue

    if len(titolo) < 10:
        continue

    titolo_lower = titolo.lower()

    # blacklist minima
    if any(b in titolo_lower for b in blacklist):
        continue

    # Cerca URL articolo WordPress:
    # /2026/03/10/titolo/

    match_data = re.search(
        r"/(\d{4})/(\d{2})/(\d{2})/",
        href
    )

    if not match_data:
        continue

    # evita duplicati
    if href in usati:
        continue

    usati.add(href)

    anno = int(match_data.group(1))
    mese = int(match_data.group(2))
    giorno = int(match_data.group(3))

    pub_date = datetime(
        anno,
        mese,
        giorno,
        tzinfo=UTC
    )

    print(f"ARTICOLO: {titolo}")

    print(
        f"DATA TROVATA: "
        f"{giorno}/{mese}/{anno}"
    )

    descrizione = titolo

    try:

        articolo_response = requests.get(
            href,
            headers=headers,
            timeout=30
        )

        articolo_response.raise_for_status()

        articolo_soup = BeautifulSoup(
            articolo_response.text,
            "html.parser"
        )

        paragrafi = articolo_soup.find_all("p")

        for p in paragrafi:

            testo = p.get_text(strip=True)

            if len(testo) > 80:

                descrizione = testo[:500]
                break

    except Exception as e:

        print(f"ERRORE ARTICOLO: {e}")

    items.append({
        "title": titolo,
        "link": href,
        "description": descrizione,
        "pubDate": pub_date
    })

items.sort(
    key=lambda x: x["pubDate"],
    reverse=True
)

print("\n========== ORDINE FINALE ==========\n")

for item in items:

    print(
        item["pubDate"].strftime("%d/%m/%Y"),
        "-",
        item["title"]
    )

print("\n===================================\n")

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
    <description>Feed RSS automatico Azienda Speciale Carlentini</description>

    {rss_items}

</channel>
</rss>
"""

output_file = os.path.abspath("feed.xml")

with open(output_file, "w", encoding="utf-8") as f:

    f.write(rss_content)

print(f"Feed creato con {len(items)} elementi")
print(f"Feed salvato in: {output_file}")