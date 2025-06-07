import os
import csv
import imagehash
from PIL import Image
from collections import defaultdict
from tqdm import tqdm
from skimage.metrics import structural_similarity as ssim
import numpy as np

# Config
CSV_FILE = "results/products_final.csv"
IMAGE_FOLDER = "images"
OUTPUT_FILE = "results/similarity_results.csv"
TOP_PHASH_CANDIDATES = 15
TOP_FINAL = 5
EXCLUDE_IDS = {"10924475"}  # Exclude known bad items

# Load phash and image
hashes = {}
images = {}
product_ids = []

def load_image_gray(path):
    img = Image.open(path).convert("L").resize((200, 200))
    return np.array(img)

with open(CSV_FILE, newline='', encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        pid = row["product_id"]
        if pid in EXCLUDE_IDS:
            continue
        path = os.path.join(IMAGE_FOLDER, f"{pid}.jpg")
        if os.path.exists(path):
            try:
                pil_img = Image.open(path).convert("RGB")
                hashes[pid] = imagehash.phash(pil_img)
                images[pid] = load_image_gray(path)
                product_ids.append(pid)
            except Exception as e:
                print(f"⚠️ Skipped {pid}: {e}")

# Step 1: Get phash candidates
combined_results = {}

for pid1 in tqdm(product_ids, desc="Comparing phash"):
    candidates = []
    for pid2 in product_ids:
        if pid1 == pid2:
            continue
        phash_dist = hashes[pid1] - hashes[pid2]
        candidates.append((pid2, phash_dist))
    
    top_candidates = sorted(candidates, key=lambda x: x[1])[:TOP_PHASH_CANDIDATES]

    # Step 2: Compute SSIM on top candidates
    ssim_scores = []
    img1 = images[pid1]
    for pid2, _ in top_candidates:
        img2 = images[pid2]
        score, _ = ssim(img1, img2, full=True)
        ssim_scores.append((pid2, score))

    final_top = sorted(ssim_scores, key=lambda x: -x[1])[:TOP_FINAL]
    combined_results[pid1] = [p[0] for p in final_top]

# Step 3: Save CSV
with open(OUTPUT_FILE, "w", newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["product_id", "similar_product_ids"])
    for pid, simlist in combined_results.items():
        writer.writerow([pid, ";".join(simlist)])

print(f"✅ Combined similarity saved to: {OUTPUT_FILE}")
