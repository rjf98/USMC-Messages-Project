
import json
import re
import unicodedata

# Load enriched JSON
with open("usmc_messages_enriched.json", "r") as f:
    messages = json.load(f)

def clean_text(text):
    if not text:
        return ""
    # Replace Unicode non-breaking spaces and other weird space variants
    text = text.replace("\u00a0", " ").replace("\xa0", " ")
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")  # remove remaining non-ascii characters
    text = re.sub(r"[ \t]+", " ", text)  # collapse extra horizontal whitespace
    text = re.sub(r"\n{2,}", "\n", text)  # collapse multiple newlines
    return text.strip()

cleaned_messages = []
for m in messages:
    m["body"] = clean_text(m.get("body", ""))
    m["title"] = clean_text(m.get("title", ""))
    cleaned_messages.append(m)

# Save to cleaned JSON
with open("usmc_messages_cleaned.json", "w") as f:
    json.dump(cleaned_messages, f, indent=2)

print(f"✅ Cleaned {len(cleaned_messages)} messages and saved to usmc_messages_cleaned.json")
