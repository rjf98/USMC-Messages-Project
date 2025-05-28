# -----------------------------------------------
# macOS users: if Chrome doesn't open or you see
# "chromedriver cannot be opened" warnings:
#
# Run this once in Terminal:
#   xattr -d com.apple.quarantine /opt/homebrew/bin/chromedriver
# -----------------------------------------------

import json
import re

INPUT_FILE = "/Volumes/1TB SSD/usmc_project/usmc_2025_message_links.json"
OUTPUT_FILE = "/Volumes/1TB SSD/usmc_project/usmc_messages_2025_enriched.json"

with open(INPUT_FILE) as f:
    messages = json.load(f)

def clean_text(text):
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u2013", "-").replace("\u2022", "-")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_metadata(message):
    content = message.get("content", "")
    title = message.get("title", "").strip()

    # Try to extract MARADMIN/ALMAR number and signed date
    msgnum = None
    signed = None

    number_match = re.search(r"(MARADMIN|ALMAR)\s+\d{3}/\d{2}", content)
    if number_match:
        msgnum = number_match.group(0)

    date_match = re.search(r"Date Signed[:\s]*([\d/]+)", content)
    if date_match:
        signed = date_match.group(1)

    return {
        "message_number": msgnum,
        "message_type": msgnum.split()[0] if msgnum else None,
        "title": title,
        "signed_date": signed,
        "url": message.get("url"),
        "content": clean_text(content)
    }

enriched = [extract_metadata(m) for m in messages]

with open(OUTPUT_FILE, "w") as f:
    json.dump(enriched, f, indent=2)

# Also save summary version
summary = [
    {
        "message_number": e["message_number"],
        "title": e["title"],
        "signed_date": e["signed_date"],
        "url": e["url"]
    }
    for e in enriched
    if e["message_number"] and e["title"]
]

with open("/Volumes/1TB SSD/usmc_project/usmc_messages_2025_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print(f"✅ Done. Enriched {len(enriched)} messages → {OUTPUT_FILE}")
