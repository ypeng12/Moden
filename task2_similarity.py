import os
import csv
import imagehash
from PIL import Image
from collections import defaultdict
from tqdm import tqdm

# Config
CSV_FILE = "results/products_final.csv"
IMAGE_FOLDER = "images"
TOP_K = 5  # Number of most similar products to find

# Step 1: Compute hashes for all images
hashes = {}
product_ids = []

with open(CSV_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        product_id = row["product_id"]
        path = os.path.join(IMAGE_FOLDER, f"{product_id}.jpg")
        if os.path.exists(path):
            try:
                img = Image.open(path).convert("RGB")
                hashes[product_id] = imagehash.phash(img)
                product_ids.append(product_id)
            except Exception as e:
                print(f"⚠️ Couldn't hash image for {product_id}: {e}")

# Step 2: Compare hashes and keep top-K
similarities = defaultdict(list)
for pid1 in tqdm(product_ids, desc="Comparing products"):
    for pid2 in product_ids:
        if pid1 == pid2:
            continue
        distance = hashes[pid1] - hashes[pid2]
        similarities[pid1].append((pid2, distance))

    similarities[pid1] = sorted(similarities[pid1], key=lambda x: x[1])[:TOP_K]

# Step 3: Save to CSV
output_file = "results/similarity_results.csv"
with open(output_file, "w", newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["product_id", "similar_product_ids"])
    for pid, simlist in similarities.items():
        ids = [s[0] for s in simlist]
        writer.writerow([pid, ";".join(ids)])

print(f"✅ Similarity results saved to: {output_file}")
