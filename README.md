from PyPDF2 import PdfReader
import markdownify
import os

# Load the PDF
pdf_path = "/mnt/data/modesens (1).pdf"
reader = PdfReader(pdf_path)

# Extract all text from the PDF
full_text = ""
for page in reader.pages:
    full_text += page.extract_text() + "\n"

# Convert the plain text to Markdown using markdownify (although it's plain text)
markdown_text = markdownify.markdownify(full_text, heading_style="ATX")

# Save as README.md
output_path = "/mnt/data/README.md"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(markdown_text)

output_path
