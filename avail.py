import csv
import re
import time
import random
import logging
from playwright.sync_api import sync_playwright, Page

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def get_avail_ids_and_urls(page: Page):
    avail_data = []
    avail_blocks = page.query_selector_all('div.avail[id^="a"]')
    logging.info(f"Found {len(avail_blocks)} avail blocks.")

    for block in avail_blocks:
        try:
            avail_id = block.get_attribute('id')
            redirect_url = f"https://modesens.cn/product/avail/{avail_id[1:]}/getlink/"
            avail_data.append((avail_id, redirect_url))
        except Exception as e:
            logging.warning(f"❌ Error processing block: {str(e)}")
            avail_data.append(("unknown", "N/A"))

    return avail_data

def scrape_modesens():
    url = "https://modesens.cn/product/zimmermann-crush-belted-embellished-floral-print-linen-mini-dress-multi-105444977/"
    product_id = re.search(r'-(\d+)/?$', url).group(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        page = context.new_page()

        logging.info("🔗 正在打开ModeSens商品页面")
        page.goto(url, timeout=60000)
        time.sleep(random.uniform(3, 5))

        try:
            cover_url = page.query_selector("meta[property='og:image']").get_attribute("content")
        except:
            cover_url = "N/A"

        data = get_avail_ids_and_urls(page)
        avail_ids = [item[0] for item in data]
        avail_urls = [item[1] for item in data]

        logging.info(f"✅ Product ID: {product_id}")
        logging.info(f"✅ Cover URL: {cover_url}")
        logging.info(f"✅ Avail IDs: {avail_ids}")
        logging.info(f"✅ Avail URLs: {avail_urls}")

        with open("product_single_final.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["product_id", "cover_url", "avail_ids", "avail_urls"])
            writer.writerow([product_id, cover_url, '|'.join(avail_ids), '|'.join(avail_urls)])

        browser.close()

if __name__ == "__main__":
    scrape_modesens()
