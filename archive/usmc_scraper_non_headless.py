
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

options = Options()
# Point to your specific Chrome for Testing binary
options.binary_location = "/Users/rich/Downloads/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

base_url = "https://www.marines.mil/News/Messages/?Page={}"

messages = []

try:
    for page in range(1, 6):  # adjust number of pages to scrape
        print(f"🌐 Scraping page {page}...")
        driver.get(base_url.format(page))
        time.sleep(5)  # wait for JS to load

        try:
            links = driver.find_elements(By.CSS_SELECTOR, "a.news-link")
            print(f"🔗 Found {len(links)} message links on page {page}")

            for link in links:
                href = link.get_attribute("href")
                title = link.text.strip()
                if href and title:
                    messages.append({
                        "title": title,
                        "url": href
                    })

        except Exception as e:
            print(f"⚠️ Error on page {page}: {e}")

finally:
    driver.quit()

with open("usmc_messages.json", "w") as f:
    json.dump(messages, f, indent=2)

print(f"✅ Saved {len(messages)} messages to usmc_messages.json")
