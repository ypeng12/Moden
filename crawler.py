import re
import csv
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(filename="crawler.log", level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def extract_product_id(url):
    match = re.search(r'-([0-9]+)/?$', url)
    return match.group(1) if match else ""

# Setup headless Chrome with user-agent spoofing
options = Options()
options.add_argument("--window-size=1280,800")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Remove Selenium webdriver flag
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
  "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

base_url = "https://modesens.cn/collections/"
products_data = []

for page in range(1, 4):
    page_url = f"{base_url}?page={page}"
    driver.get(page_url)
    time.sleep(random.uniform(2, 4))

    # Attempt to dismiss login popup
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.ESCAPE)
        time.sleep(1)
    except Exception as e:
        logging.warning(f"ESC to close popup failed: {e}")

    # Gather product links on the listing page
    product_link_elems = driver.find_elements(By.XPATH, "//a[contains(@href, '/product/')]")
    product_links = []

    for elem in product_link_elems:
        try:
            href = elem.get_attribute("href")
            if not href:
                continue
            try:
                img = elem.find_element(By.TAG_NAME, "img")
                img_src = img.get_attribute("src")
            except:
                img_src = ""
            product_links.append((href, img_src))
        except Exception as e:
            logging.warning(f"Link extraction failed: {e}")

    # Visit each product page (note: availability may be blocked)
    for product_url, cover_url in product_links:
        product_id = extract_product_id(product_url)
        if not product_id:
            continue

        try:
            driver.get(product_url)
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            logging.warning(f"Failed to load product page: {product_url}, error: {e}")
            continue

        # Check for captcha or block
        if "captcha" in driver.page_source.lower() or "403" in driver.title:
            logging.warning(f"Captcha or block on product {product_url}. Skipping.")
            continue

        # Extract availability info (may be blocked)
        availability_ids = []
        availability_urls = []

        try:
            buy_links = driver.find_elements(By.XPATH, "//a[contains(text(), '浏览商店')]")
            for idx, a in enumerate(buy_links):
                url = a.get_attribute("href")
                availability_urls.append(url or "")
                availability_ids.append(f"store_{idx+1}")
        except:
            pass  # silently skip if missing

        products_data.append({
            "product_id": product_id,
            "avail_ids": ";".join(availability_ids),
            "product_cover_url": cover_url,
            "avail_urls": ";".join(availability_urls),
        })

        logging.info(f"Saved product {product_id} with {len(availability_ids)} availabilities.")
        time.sleep(random.uniform(2, 5))

# Save to CSV
with open("products.csv", "w", newline='', encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["product_id", "avail_ids", "product_cover_url", "avail_urls"])
    writer.writeheader()
    for row in products_data:
        writer.writerow(row)

driver.quit()
print(f"✅ Done. Saved {len(products_data)} products to products.csv.")
