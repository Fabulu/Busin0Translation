"""Extract all text from the English guide PDF using PyMuPDF."""
import fitz
import os
import time

PDF_PATH = r"C:\Programmieren\wizardrytranslation\ENGLISH GUIDE.pdf"
PAGE_DIR = r"C:\Programmieren\wizardrytranslation\data\guide_text"
COMBINED  = r"C:\Programmieren\wizardrytranslation\data\guide_full_text.txt"

os.makedirs(PAGE_DIR, exist_ok=True)

print(f"Opening PDF: {PDF_PATH}")
t0 = time.time()
doc = fitz.open(PDF_PATH)
total_pages = len(doc)
print(f"Total pages: {total_pages}")

total_chars = 0
combined_parts = []

for i, page in enumerate(doc):
    text = page.get_text("text")
    total_chars += len(text)
    combined_parts.append(text)

    page_file = os.path.join(PAGE_DIR, f"page_{i+1:03d}.txt")
    with open(page_file, "w", encoding="utf-8") as f:
        f.write(text)

    if (i + 1) % 50 == 0 or i == 0 or i == total_pages - 1:
        elapsed = time.time() - t0
        print(f"  Page {i+1}/{total_pages}  ({elapsed:.1f}s elapsed, {total_chars:,} chars so far)")

with open(COMBINED, "w", encoding="utf-8") as f:
    for part in combined_parts:
        f.write(part)

elapsed = time.time() - t0
print(f"\nDone in {elapsed:.1f}s")
print(f"Total pages: {total_pages}")
print(f"Total characters: {total_chars:,}")
print(f"Combined file: {COMBINED}")
print(f"Page files: {PAGE_DIR}/page_001.txt .. page_{total_pages:03d}.txt")
