import os
import csv
import logging
import requests
from PIL import Image
import imagehash
import numpy as np
from skimage.metrics import structural_similarity as ssim

# Configure logging
logging.basicConfig(
    filename="image_analysis.log", level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Directory to cache images
IMAGE_DIR = "images"
if not os.path.isdir(IMAGE_DIR):
    os.makedirs(IMAGE_DIR, exist_ok=True)

def download_image(url: str, save_path: str) -> bool:
    """Download an image from URL to the given path. Returns True if successful or already cached."""
    if os.path.exists(save_path):
        logging.info(f"Image already cached: {save_path}")
        return True
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(resp.content)
            logging.info(f"Downloaded image: {url} -> {save_path}")
            return True
        else:
            logging.error(f"Failed to download image (status {resp.status_code}): {url}")
    except Exception as e:
        logging.error(f"Exception downloading {url}: {e}")
    return False

def compute_hash_similarity(img1: Image.Image, img2: Image.Image) -> float:
    """Compute perceptual hash similarity (as 1 - normalized Hamming distance) between two images."""
    hash1 = imagehash.phash(img1)
    hash2 = imagehash.phash(img2)
    # Hamming distance between hashes (0 means identical hashes)
    diff = hash1 - hash2
    hash_size = hash1.hash.size  # total bits in hash (e.g., 64 for default 8x8 phash)
    similarity = 1 - (diff / hash_size)  # normalize to [0,1], 1 = identical
    return round(similarity, 3)  # round to 3 decimal places for display

def compute_ssim(img1: Image.Image, img2: Image.Image) -> float:
    """Compute SSIM between two images (grayscale). Returns SSIM value in [0,1]."""
    # Convert images to grayscale
    img1_gray = np.array(img1.convert("L"))
    img2_gray = np.array(img2.convert("L"))
    # Resize second image to match first image dimensions
    if img1_gray.shape != img2_gray.shape:
        img2_gray = np.array(Image.fromarray(img2_gray).resize((img1_gray.shape[1], img1_gray.shape[0])))
    try:
        score = ssim(img1_gray, img2_gray, data_range=img1_gray.max() - img1_gray.min())
    except Exception as e:
        logging.error(f"SSIM computation error: {e}")
        return 0.0
    return round(score, 3)

# Read the CSV data from crawler
products = []
with open("products.csv", newline='', encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        products.append({
            "product_id": row["product_id"],
            "cover_url": row["product_cover_url"],
            "avail_ids": row["avail_ids"].split(';') if row["avail_ids"] else [],
            "avail_urls": row["avail_urls"].split(';') if row["avail_urls"] else []
        })

# Data structure to hold results for HTML
results = []  # list of dict per product with images and similarity scores

for prod in products:
    pid = prod["product_id"]
    cover_url = prod["cover_url"]
    avail_ids = prod["avail_ids"]
    avail_urls = prod["avail_urls"]
    if not cover_url or not avail_urls:
        logging.warning(f"Skipping product {pid}: missing cover or availability URLs.")
        continue

    # File paths for images
    cover_path = os.path.join(IMAGE_DIR, f"{pid}_cover.jpg")
    # Download cover image if needed
    if not download_image(cover_url, cover_path):
        logging.error(f"Could not get cover image for product {pid}, skipping.")
        continue

    # Open cover image with PIL
    try:
        cover_img = Image.open(cover_path)
    except Exception as e:
        logging.error(f"Cannot open cover image for {pid}: {e}")
        continue

    product_result = {
        "product_id": pid,
        "cover_path": cover_path,
        "comparisons": []  # will hold dicts of availability image data and similarity scores
    }

    # Track best match (highest SSIM)
    best_ssim = -1.0
    best_index = -1

    for idx, (aid, aurl) in enumerate(zip(avail_ids, avail_urls)):
        if not aurl:
            continue
        # Normalize a valid filename for the availability image
        safe_id = aid if aid else f"avail{idx+1}"
        safe_id = "".join(c for c in safe_id if c.isalnum() or c in "_-")  # remove special chars for filename
        avail_path = os.path.join(IMAGE_DIR, f"{pid}_{safe_id}.jpg")
        # Download availability image if not cached
        download_image(aurl, avail_path)
        # Open and compute similarities
        try:
            avail_img = Image.open(avail_path)
        except Exception as e:
            logging.error(f"Cannot open availability image for {pid} ({aid}): {e}")
            continue

        # Compute perceptual hash similarity and SSIM
        hash_sim = compute_hash_similarity(cover_img, avail_img)
        ssim_val = compute_ssim(cover_img, avail_img)
        # Update best match if this has higher SSIM
        if ssim_val > best_ssim:
            best_ssim = ssim_val
            best_index = idx

        product_result["comparisons"].append({
            "avail_id": aid,
            "avail_path": avail_path,
            "hash_sim": hash_sim,
            "ssim": ssim_val
        })
        logging.info(f"Product {pid} - Compared cover with {aid}: pHash sim={hash_sim}, SSIM={ssim_val}")

    # Mark which availability is the best match
    product_result["best_index"] = best_index
    results.append(product_result)

# Generate the static HTML report
html_file = "similarity_report.html"
try:
    with open(html_file, "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html><head><meta charset='UTF-8'>\n")
        f.write("<title>ModeSens Image Similarity Report</title>\n")
        # Basic inline CSS for layout and highlight
        f.write("<style>\n")
        f.write("body { font-family: Arial, sans-serif; }\n")
        f.write(".product { margin-bottom: 50px; }\n")
        f.write(".cover-img { max-width: 200px; display: block; margin-bottom: 10px; }\n")
        f.write(".avail-img { max-width: 150px; margin: 5px; border: 3px solid transparent; }\n")
        f.write(".avail-img.highlight { border-color: #4CAF50; }\n")  # green border for highlight
        f.write(".sim-table { border-collapse: collapse; }\n")
        f.write(".sim-table th, .sim-table td { border: 1px solid #ccc; padding: 5px; text-align: center; }\n")
        f.write("</style>\n</head><body>\n")
        f.write("<h1>ModeSens Product Image Similarity Report</h1>\n")

        for prod in results:
            pid = prod["product_id"]
            f.write(f"<div class='product'>\n")
            f.write(f"<h2>Product ID: {pid}</h2>\n")
            # Embed cover image
            f.write(f"<img class='cover-img' src='{prod['cover_path']}' alt='Cover Image {pid}' />\n")
            # Table of availability images and scores
            f.write("<table class='sim-table'>\n")
            f.write("<tr><th>Retailer</th><th>Image</th><th>Hash Similarity</th><th>SSIM</th></tr>\n")
            for idx, comp in enumerate(prod["comparisons"]):
                aid = comp["avail_id"] or f"Store {idx+1}"
                hash_sim = comp["hash_sim"]
                ssim_val = comp["ssim"]
                # Highlight row/image if this is the best match
                highlight_class = " highlight" if idx == prod.get("best_index") else ""
                f.write("<tr>")
                f.write(f"<td>{aid}</td>")
                f.write(f"<td><img class='avail-img{highlight_class}' src='{comp['avail_path']}' alt='{aid}' /></td>")
                f.write(f"<td>{hash_sim}</td>")
                f.write(f"<td>{ssim_val}</td>")
                f.write("</tr>\n")
            f.write("</table>\n")
            f.write("</div>\n")
        f.write("</body></html>\n")
    print(f"Image similarity report generated: {html_file}")
    logging.info(f"HTML report generated: {html_file}")
except Exception as e:
    logging.error(f"Failed to write HTML report: {e}")
    print("Error: Could not write HTML report.")
