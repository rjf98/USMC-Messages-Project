
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

# Configure Chrome
chrome_path = "/Users/rich/Downloads/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
options = Options()
options.binary_location = chrome_path
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

service = Service("/usr/local/bin/chromedriver")

try:
    driver = webdriver.Chrome(service=service, options=options)
except WebDriverException as e:
    print(f"❌ WebDriver initialization failed: {e}")
    exit(1)

base_url = "https://www.marines.mil/News/Messages/?Page={}"
messages = []

for page in range(1, 6):  # Adjust number of pages as needed
    print(f"🌐 Scraping page {page}...")
    try:
        driver.get(base_url.format(page))
        time.sleep(5)
        links = driver.find_elements(By.CSS_SELECTOR, "a.news-link")
        print(f"🔗 Found {len(links)} message links on page {page}")
        for link in links:
            try:
                url = link.get_attribute("href")
                title = link.text.strip()
                messages.append({"title": title, "url": url})
            except Exception as e:
                print(f"⚠️ Error processing a message link: {e}")
    except Exception as e:
        print(f"⚠️ Error scraping page {page}: {e}")

driver.quit()

with open("usmc_messages.json", "w") as f:
    json.dump(messages, f, indent=2)

print(f"✅ Saved {len(messages)} messages to usmc_messages.json")
