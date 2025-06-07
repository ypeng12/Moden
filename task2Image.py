import os
import csv
import requests
from tqdm import tqdm

os.makedirs("images", exist_ok=True)

csv_file = "results/products_final.csv"


with open(csv_file, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

for row in tqdm(rows, desc="Downloading images"):
    product_id = row["product_id"]
    cover_url = row["cover_url"]

    if not product_id or not cover_url:
        continue

    output_path = f"images/{product_id}.jpg"

    if os.path.exists(output_path):
        continue  # skip if already downloaded

    try:
        response = requests.get(cover_url, timeout=10)
        if response.status_code == 200:
            with open(output_path, "wb") as out:
                out.write(response.content)
    except Exception as e:
        print(f"Failed to download image for {product_id}: {e}")
