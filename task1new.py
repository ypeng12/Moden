import os
import csv
import re
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# === Setup ===
os.makedirs("results", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("results/crawler_final.log", mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
    # Add more realistic user agents
]

# === Chrome Options ===
options = Options()
options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
w, h = random.randint(1200, 1400), random.randint(700, 900)
options.add_argument(f"--window-size={w},{h}")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--headless=new")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined})
    """
})
driver.set_page_load_timeout(25)

# === Manual Login Step ===
login_url = "https://modesens.cn/collections/"
driver.get(login_url)
input("🔐 请手动完成登录（验证码或账户）。完成后按 [ENTER] 继续...")

# === CSV Output ===
csv_path = "results/products_final.csv"
csv_fields = ["product_id", "cover_url", "avail_ids", "avail_urls"]
csv_file = open(csv_path, "w", newline='', encoding="utf-8")
csv_writer = csv.DictWriter(csv_file, fieldnames=csv_fields)
csv_writer.writeheader()

def extract_product_id(url):
    match = re.search(r'-([0-9]+)/?$', url)
    return match.group(1) if match else ""

def human_scroll(driver):
    scroll_pause = random.uniform(0.5, 1.5)
    height = driver.execute_script("return document.body.scrollHeight")
    for y in range(0, height, 400):
        driver.execute_script(f"window.scrollTo(0, {y});")
        time.sleep(scroll_pause)

def safe_get(url, retries=3, wait_on_block=True):
    for attempt in range(retries):
        try:
            driver.get(url)
            if "403" in driver.title or "登录" in driver.title or "captcha" in driver.page_source.lower():
                logging.warning(f"🔐 CAPTCHA or block detected: {url}")
                if wait_on_block:
                    input("🛑 请手动解决问题后按 [ENTER] 继续...")
                else:
                    time.sleep(2 ** attempt + random.uniform(0.5, 1.5))
                continue
            return True
        except Exception as e:
            logging.warning(f"⚠️ Error on attempt {attempt+1}/{retries}: {e}")
            time.sleep(2 ** attempt)
    return False

# === Crawl ===
try:
    for page in range(1, 4):
        url = f"https://modesens.cn/collections/?page={page}"
        logging.info(f"🔗 Visiting: {url}")
        if not safe_get(url):
            continue

        human_scroll(driver)
        time.sleep(random.uniform(2, 3.5))

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.prdcard-wrapper a"))
            )
        except Exception as e:
            logging.warning(f"⚠️ Product links not found on page {page}: {e}")
            continue

        product_links = []
        for link in driver.find_elements(By.CSS_SELECTOR, "div.prdcard-wrapper a"):
            href = link.get_attribute("href")
            if not href or "/product/" not in href:
                continue
            try:
                img = link.find_element(By.TAG_NAME, "img")
                img_src = img.get_attribute("src") or ""
            except:
                img_src = ""
            product_links.append((href, img_src))

        logging.info(f"📦 Page {page} contains {len(product_links)} products.")

        for product_url, cover_url in product_links:
            product_id = extract_product_id(product_url)
            if not product_id:
                continue

            if not safe_get(product_url):
                continue

            time.sleep(random.uniform(2.0, 3.0))
            human_scroll(driver)
            time.sleep(1.5)

            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.avail[id^='a']"))
                )
            except TimeoutException:
                logging.warning(f"⚠️ No availabilities found for {product_id}")

            avail_ids, avail_urls = [], []
            for avail in driver.find_elements(By.CSS_SELECTOR, "div.avail[id^='a']"):
                aid = avail.get_attribute("id")
                if aid:
                    avail_ids.append(aid)
                    avail_urls.append(f"https://modesens.cn/product/avail/{aid[1:]}/getlink/")

            csv_writer.writerow({
                "product_id": product_id,
                "cover_url": cover_url,
                "avail_ids": ";".join(avail_ids),
                "avail_urls": ";".join(avail_urls)
            })
            logging.info(f"✅ Saved product {product_id} with {len(avail_ids)} availabilities.")
            time.sleep(random.uniform(1.5, 2.5))

finally:
    driver.quit()
    csv_file.close()
    logging.info("🎉 Done. All results saved to products_final.csv")
