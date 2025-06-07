import os
import csv
import requests
from PIL import Image
from io import BytesIO
import imagehash
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

# Setup folders
os.makedirs("images/product", exist_ok=True)
os.makedirs("images/avail", exist_ok=True)

def download_image(url, save_path):
    if os.path.exists(save_path):
        return save_path
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(r.content)
            return save_path
    except:
        pass
    return None

def compute_similarity(img1_path, img2_path):
    try:
        # dHash
        hash1 = imagehash.dhash(Image.open(img1_path).convert("RGB"))
        hash2 = imagehash.dhash(Image.open(img2_path).convert("RGB"))
        dhash_diff = hash1 - hash2

        # SSIM
        img1 = cv2.imread(img1_path)
        img2 = cv2.imread(img2_path)
        img1 = cv2.resize(img1, (200, 200))
        img2 = cv2.resize(img2, (200, 200))
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        ssim_score = ssim(gray1, gray2)
        return dhash_diff, ssim_score
    except Exception as e:
        return None, None

# Read input CSV
html_rows = []
with open("results/products_final.csv", newline='', encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        pid = row["product_id"]
        cover_url = row["cover_url"]
        avail_urls = row["avail_urls"].split(";")

        product_img = f"images/product/{pid}.jpg"
        download_image(cover_url, product_img)

        comparison_rows = []
        best_score = -1
        best_html = ""

        for i, a_url in enumerate(avail_urls):
            aid = f"{pid}_{i}"
            a_img = f"images/avail/{aid}.jpg"
            download_image(a_url, a_img)

            dhash_diff, ssim_score = compute_similarity(product_img, a_img)
            if dhash_diff is None or ssim_score is None:
                continue

            html_block = f"""
            <td>
                <img src="../{a_img}" height="120"><br>
                <b>SSIM:</b> {ssim_score:.3f}<br>
                <b>dHash Δ:</b> {dhash_diff}
            </td>
            """
            comparison_rows.append((ssim_score, html_block))

        # Sort by best match
        comparison_rows.sort(key=lambda x: -x[0])  # SSIM descending

        row_html = f"""
        <tr>
            <td><b>{pid}</b><br><img src="../{product_img}" height="150"></td>
            {''.join(html for _, html in comparison_rows)}
        </tr>
        """
        html_rows.append(row_html)

# Build HTML
html = f"""
<html>
<head>
    <title>Task 2 - Image Similarity Viewer</title>
    <style>
        body {{ font-family: sans-serif; }}
        table {{ border-collapse: collapse; width: 100%; }}
        td {{ border: 1px solid #ccc; padding: 10px; text-align: center; }}
        img {{ border-radius: 4px; }}
    </style>
</head>
<body>
    <h1>🧠 Product vs Availability Cover Similarity</h1>
    <table>
        <tr>
            <th>Product</th>
            <th colspan="5">Availability Covers + Scores</th>
        </tr>
        {''.join(html_rows)}
    </table>
</body>
</html>
"""

# Save HTML file
with open("results/task2_similarity_report.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ HTML report saved to: results/task2_similarity_report.html")
