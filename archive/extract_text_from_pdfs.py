import os
import json
import fitz  # PyMuPDF
import re

# Known URLs mapped to filenames
pdf_urls = {
    "01_officer_candidates_school_physical_fitness_test_induction_and.pdf":
        "https://www.marines.mil/News/Messages/Messages-Display/Article/4188275/officer-candidates-school-physical-fitness-test-induction-and-graduation-standa/",
    "02_armed_forces_day.pdf":
        "https://www.marines.mil/News/Messages/Messages-Display/Article/4188879/armed-forces-day/",
    "03_announcement_of_the_calendar_year_2024_male_and.pdf":
        "https://www.marines.mil/News/Messages/Messages-Display/Article/4187836/announcement-of-the-calendar-year-2024-male-and-female-athletes-of-the-year/",
    "04_cancellation_of_maradmin_229_22.pdf":
        "https://www.marines.mil/News/Messages/Messages-Display/Article/4187760/cancellation-of-maradmin-229-22/",
    "05_announcement_of_reserve_sergeants_major_slate_for_calendar.pdf":
        "https://www.marines.mil/News/Messages/Messages-Display/Article/4187616/announcement-of-reserve-sergeants-major-slate-for-calendar-year-20252026-cy25cy/"
}

def extract_title(text):
    lines = text.splitlines()
    title_lines = []
    started = False
    for line in lines:
        stripped = line.strip()
        if not started and stripped.isupper() and len(stripped) > 10:
            started = True
        if started:
            if stripped == "" or "Date Signed" in stripped:
                break
            title_lines.append(stripped)
        if len(title_lines) >= 8:
            break
    return " ".join(title_lines).title() if title_lines else "Untitled"

def extract_metadata(text):
    msg_type = "UNKNOWN"
    msg_number = "?"
    msg_date = "Unknown Date"

    match = re.search(r"\b(MARADMIN|ALMAR)(?:\s+CANCELLATION)?\s+([0-9]{3}/[0-9]{2})\b", text.upper())
    if match:
        msg_type = match.group(1)
        msg_number = match.group(2)

    date_match = re.search(r"Date Signed[:\-]?\s*([0-9/]+)", text, re.IGNORECASE)
    if date_match:
        msg_date = date_match.group(1)

    return msg_type, msg_number, msg_date

pdf_dir = "maradmin_pdfs"
messages = []

for filename in sorted(os.listdir(pdf_dir)):
    if filename.lower().endswith(".pdf"):
        path = os.path.join(pdf_dir, filename)
        try:
            with fitz.open(path) as doc:
                text = "\n".join(page.get_text() for page in doc)

            title = extract_title(text)
            msg_type, msg_number, msg_date = extract_metadata(text)
            url = pdf_urls.get(filename, None)

            messages.append({
                "title": title,
                "category": msg_type,
                "number": msg_number,
                "date": msg_date,
                "filename": filename,
                "url": url,
                "content": text.strip()
            })
            print(f"✅ Extracted: {filename}")
        except Exception as e:
            print(f"❌ Failed to process {filename}: {e}")

# Save to JSON
with open("usmc_messages.json", "w") as f:
    json.dump(messages, f, indent=2)

print(f"\n📦 Done. Saved {len(messages)} messages to usmc_messages.json")
