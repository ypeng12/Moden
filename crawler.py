import re
import csv
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Logging configuration
logging.basicConfig(
    filename="crawler.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def extract_product_id(url: str) -> str:
    match = re.search(r'-([0-9]+)/?$', url)
    return match.group(1) if match else ""

# Chrome setup (non-headless is safer for debugging)
options = Options()
# Comment out headless for visual debugging:
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1280,800")
options.add_argument("user-agent=Mozilla/5.0")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.set_page_load_timeout(15)

base_url = "https://modesens.cn/collections/"
products_data = []

for page in range(1, 4):
    page_url = f"{base_url}?page={page}"
    logging.info(f"Fetching collections page {page}: {page_url}")
    try:
        driver.get(page_url)
        time.sleep(random.uniform(2, 3))
    except Exception as e:
        logging.error(f"Error loading page {page_url}: {e}")
        continue

    try:
        link_elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/product/')]")
        logging.info(f"Found {len(link_elements)} product links on page {page}")
    except Exception as e:
        logging.error(f"Failed to extract product links: {e}")
        continue

    # Extract href and img first to avoid stale reference
    page_products = []
    for elem in link_elements:
        try:
            href = elem.get_attribute("href")
            if not href or "/product/" not in href:
                continue
            product_id = extract_product_id(href)
            img_src = ""
            try:
                img = elem.find_element(By.TAG_NAME, "img")
                img_src = img.get_attribute("src") or img.get_attribute("data-src") or ""
            except:
                pass
            page_products.append((product_id, href, img_src))
        except Exception as e:
            logging.warning(f"Failed to extract from element: {e}")
            continue

    # Visit each product page
    for product_id, product_url, cover_url in page_products:
        logging.info(f"Visiting product {product_id} -> {product_url}")
        avail_ids = []
        avail_urls = []

        try:
            driver.get(product_url)
            time.sleep(random.uniform(2, 3))
        except Exception as e:
            logging.error(f"Could not load product page {product_url}: {e}")
            continue

        page_source = driver.page_source.lower()
        if "captcha" in page_source or "验证" in page_source:
            logging.warning(f"Blocked on product page {product_url}. Skipping availability.")
        else:
            try:
                buy_links = driver.find_elements(By.XPATH, "//a[contains(text(), '浏览商店')]")
                for idx, a in enumerate(buy_links):
                    url = a.get_attribute("href")
                    if url:
                        avail_urls.append(url)
                        avail_ids.append(f"store_{idx+1}")
            except Exception as e:
                logging.warning(f"Error extracting availabilities for {product_id}: {e}")

        products_data.append({
            "product_id": product_id,
            "avail_ids": ";".join(avail_ids),
            "product_cover_url": cover_url,
            "avail_urls": ";".join(avail_urls)
        })

        time.sleep(random.uniform(1, 2))

driver.quit()

# Save to CSV
csv_file = "products.csv"
with open(csv_file, "w", newline='', encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["product_id", "avail_ids", "product_cover_url", "avail_urls"])
    writer.writeheader()
    for row in products_data:
        writer.writerow(row)

print(f"✅ Done. {len(products_data)} products saved to products.csv.")
