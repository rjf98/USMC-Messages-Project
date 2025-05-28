# -----------------------------------------------
# macOS users: if Chrome doesn't open or you see
# "chromedriver cannot be opened" warnings:
#
# Run this once in Terminal:
#   xattr -d com.apple.quarantine /opt/homebrew/bin/chromedriver
# -----------------------------------------------

import json
import re
import time
import os
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Path to Chrome for Testing (update if needed)
CHROME_PATH = "/Users/rich/Downloads/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
CHROMEDRIVER_PATH = "/opt/homebrew/bin/chromedriver"

# Setup Chrome options
chrome_options = Options()
chrome_options.binary_location = CHROME_PATH
chrome_options.add_argument("--headless")  # Enable headless mode for background execution
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Start Chrome driver
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Load original JSON
with open("usmc_messages.json", "r") as f:
    raw_data = json.load(f)

unique_urls = sorted(set(entry["url"] for entry in raw_data))
enriched_messages = []

# Ensure screenshot folder exists
os.makedirs("screenshots", exist_ok=True)

for i, url in enumerate(tqdm(unique_urls, desc="Enriching messages")):
    try:
        print(f"\nFetching: {url}")

        # Extract Article ID from the original URL
        match = re.search(r"/Article/(\d+)/", url)
        if not match:
            raise ValueError("No Article ID found in URL")

        article_id = match.group(1)
        print_url = f"https://www.marines.mil/DesktopModules/ArticleCS/Print.aspx?PortalId=1&ModuleId=542&Article={article_id}"

        driver.get(print_url)

        # Wait until the print body loads
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(1.0)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "Unknown"

        body_tag = soup.find("div", class_="body") or soup.find("article") or soup.find("main")
        body = body_tag.get_text(separator="\n", strip=True) if body_tag else soup.get_text(strip=True)

        # Fallback title from first line of body
        if title == "Unknown" and body:
            first_line = next((line.strip() for line in body.splitlines() if line.strip()), None)
            if first_line:
                title = first_line

        # Extract date from body if not found earlier
        date_match = re.search(r"Date Signed:\s*(\d{1,2}/\d{1,2}/\d{4})", body)
        date = date_match.group(1) if date_match else None

        print(f"  ➤ Title: {title}")
        print(f"  ➤ Body length: {len(body)} characters")

        driver.save_screenshot(f"screenshots/print_page_{i+1}.png")

        message_number = None
        for text in [title, body]:
            if text:
                match = re.search(r"(MARADMIN|ALMAR)\s+\d{3}/\d{2}", text)
                if match:
                    message_number = match.group()
                    break

        enriched_messages.append({
            "message_number": message_number,
            "title": title,
            "date": date,
            "url": url,
            "body": body
        })

    except Exception as e:
        print(f"❌ Error processing {url}: {e}")
        with open("enrichment_errors.log", "a") as log:
            log.write(f"{url}\n")

# Quit browser
driver.quit()

# Save output
with open("usmc_messages_enriched.json", "w") as f:
    json.dump(enriched_messages, f, indent=2)

print(f"\n✅ Enriched {len(enriched_messages)} unique messages saved to usmc_messages_enriched.json")
