
import csv
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = (
    "https://sourcing.alibaba.com/rfq/rfq_search_list.htm"
    "?country=AE&recently=Y&tracelog=newest&pageSize=20"
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0 Safari/537.36"
    )
}

OUT_FILE = "alibaba_rfq_AE_recent.csv"
FIELDNAMES = [
    "rfq_id",
    "title",
    "quantity",
    "unit",
    "purchase_frequency",
    "posted_date",
    "expiry_date",
    "categories",
    "buyer_country",
    "buyer_name",
    "buyer_membership_level",
    "rfq_url",
]

def fetch_page(page: int) -> str:
    url = f"{BASE_URL}&page={page}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text

def parse_rfq_card(card) -> dict:
    rfq_url = urljoin("https://sourcing.alibaba.com", card.select_one("a").get("href"))
    rfq_id = rfq_url.split("rfqId=")[-1]

    title = card.select_one(".rfq-item-title").get_text(strip=True)

    qty_block = card.select_one(".rfq-quantity").get_text(" ", strip=True)
    qty_parts = qty_block.split()
    quantity = qty_parts[0]
    unit = " ".join(qty_parts[1:])

    purchase_frequency = (
        card.select_one(".rfq-frequency").get_text(strip=True) if card.select_one(".rfq-frequency") else ""
    )

    posted_date = card.select_one(".rfq-posttime")["data-date"]
    expiry_date = card.select_one(".rfq-expiretime")["data-date"]

    categories = card.select_one(".rfq-category").get_text(" > ", strip=True)
    buyer_country = card.select_one(".buyer-country").get_text(strip=True)
    buyer_name = card.select_one(".buyer-name").get_text(strip=True)
    buyer_membership_level = (
        card.select_one(".buyer-level").get_text(strip=True) if card.select_one(".buyer-level") else ""
    )

    return {
        "rfq_id": rfq_id,
        "title": title,
        "quantity": quantity,
        "unit": unit,
        "purchase_frequency": purchase_frequency,
        "posted_date": posted_date,
        "expiry_date": expiry_date,
        "categories": categories,
        "buyer_country": buyer_country,
        "buyer_name": buyer_name,
        "buyer_membership_level": buyer_membership_level,
        "rfq_url": rfq_url,
    }

def scrape_all():
    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()

        page = 1
        while True:
            html = fetch_page(page)
            soup = BeautifulSoup(html, "lxml")
            cards = soup.select("li.rfq-item")
            if not cards:
                break

            for card in cards:
                try:
                    writer.writerow(parse_rfq_card(card))
                except Exception as e:
                    print("Skipped a card due to error:", e)

            print(f"✓ Page {page} scraped – {len(cards)} RFQs")
            page += 1
            time.sleep(1.5)

    print("All done →", OUT_FILE)

if __name__ == "__main__":
    scrape_all()
