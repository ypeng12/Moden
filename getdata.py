import os
import time
import csv
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver  # for header control

# === Chrome Setup ===
options = Options()
options.add_argument("--window-size=1280,800")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

seleniumwire_options = {
    "exclude_hosts": [
        "cdn.shopify.com", "images.lvrcdn.com", "img.the-fashion-square.com",
        "img.mytheresa.com", "product-image-sts.intramirror.com",
        "www.24s.com", "is4.fwrdassets.com", "analytics.google.com",
        "google.com", "googletagmanager.com", "static.klaviyo.com"
    ]
}

# === Driver Init ===
driver = webdriver.Chrome(options=options, seleniumwire_options=seleniumwire_options)
driver.set_page_load_timeout(25)

# === CSV Setup ===
os.makedirs("results", exist_ok=True)
csv_path = "results/data.csv"
csv_fields = ["product_id", "cover_url", "avail_ids", "avail_urls"]
csv_file = open(csv_path, "w", newline='', encoding="utf-8")
csv_writer = csv.DictWriter(csv_file, fieldnames=csv_fields)
csv_writer.writeheader()

def human_scroll():
    height = driver.execute_script("return document.body.scrollHeight")
    for y in range(0, height, 400):
        driver.execute_script(f"window.scrollTo(0, {y});")
        time.sleep(0.5)

def extract_product(product_id):
    url = f"https://modesens.cn/product/{product_id}/"
    driver.get(url)
    input("🧭 请滑动页面、处理验证码，加载完毕后按 [ENTER]...")

    human_scroll()
    time.sleep(1.5)

    try:
        img = driver.find_element(By.CSS_SELECTOR, "img")
        cover_url = img.get_attribute("src") or ""
    except:
        cover_url = ""

    avail_ids, avail_urls = [], []
    for avail in driver.find_elements(By.CSS_SELECTOR, "div.avail[id^='a']"):
        aid = avail.get_attribute("id")
        if aid:
            avail_ids.append(aid)
            avail_urls.append(f"https://modesens.cn/product/avail/{aid[1:]}/getlink/")

    print("\n📦 结果如下：")
    print("product_id:", product_id)
    print("cover_url:", cover_url)
    print("avail_ids:", ";".join(avail_ids))
    print("avail_urls:", ";".join(avail_urls))

    # 写入 CSV
    csv_writer.writerow({
        "product_id": product_id,
        "cover_url": cover_url,
        "avail_ids": ";".join(avail_ids),
        "avail_urls": ";".join(avail_urls)
    })
    print(f"✅ 已保存到 {csv_path}")

if __name__ == "__main__":
    pid = input("请输入 product_id（如：109582629）: ").strip()
    extract_product(pid)
    csv_file.close()
    driver.quit()
