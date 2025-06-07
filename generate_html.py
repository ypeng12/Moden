import csv
import os

PRODUCT_CSV = "results/products_final.csv"
SIMILARITY_CSV = "results/similarity_results.csv"
OUTPUT_HTML = "similarity_report.html"

# Load product cover URLs
product_images = {}
with open(PRODUCT_CSV, newline='', encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        product_images[row["product_id"]] = row["cover_url"]

# Load similarity results
similar_data = {}
with open(SIMILARITY_CSV, newline='', encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        pid = row[0]
        sim_ids = row[1].split(";") if len(row) > 1 else []
        similar_data[pid] = sim_ids

# Start HTML
title = "Product Similarity Viewer"
html = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
    h1 {{ text-align: center; }}
    .product-block {{
      background: white;
      padding: 20px;
      margin: 20px auto;
      border-radius: 10px;
      max-width: 1000px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }}
    .product-title {{ font-weight: bold; font-size: 18px; margin-bottom: 10px; }}
    .images {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      gap: 12px;
    }}
    .images a {{ text-align: center; text-decoration: none; color: black; }}
    .images img {{
      height: 120px;
      border-radius: 8px;
      border: 2px solid #ccc;
      transition: transform 0.2s;
    }}
    .images img:hover {{
      transform: scale(1.05);
      border-color: #4caf50;
    }}
    .highlight {{
      border-color: orange !important;
      box-shadow: 0 0 8px orange;
    }}
    .caption {{
      font-size: 12px;
      margin-top: 4px;
    }}
  </style>
</head>
<body>
<h1>\U0001f50d {title}</h1>
"""

# Generate blocks
for pid, sim_ids in similar_data.items():
    if pid not in product_images:
        continue

    html += f'<div class="product-block">\n'
    html += f'<div class="product-title">Main Product: <a href="https://modesens.cn/product/{pid}/" target="_blank">{pid}</a></div>\n'
    html += '<div class="images main">\n'
    html += f'<a href="https://modesens.cn/product/{pid}/" target="_blank">'
    html += f'<img src="{product_images[pid]}" alt="{pid}" class="highlight"><div class="caption">{pid}</div></a>\n'
    html += '</div>\n'

    html += f'<div class="product-title">Top {len(sim_ids)} Similar Products:</div>\n'
    html += '<div class="images">\n'
    for i, sid in enumerate(sim_ids):
        if sid in product_images:
            cls = "highlight" if i == 0 else ""
            html += f'<a href="https://modesens.cn/product/{sid}/" target="_blank">'
            html += f'<img src="{product_images[sid]}" class="{cls}" alt="{sid}"><div class="caption">{sid}</div></a>\n'
    html += '</div></div>\n'

# End HTML
html += "</body></html>"

# Save output
with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Report generated: {OUTPUT_HTML}")
