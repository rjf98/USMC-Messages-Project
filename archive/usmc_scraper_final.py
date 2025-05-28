
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Set up Chrome options
options = Options()
options.binary_location = "/Users/rich/Downloads/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
options.add_argument("--disable-gpu")

# Initialize the driver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

base_url = "https://www.marines.mil/News/Messages/?Page={}"
message_data = []

try:
    for page in range(1, 6):  # Adjust number of pages as needed
        print(f"🌐 Scraping page {page}...")
        driver.get(base_url.format(page))
        time.sleep(10 if page == 1 else 5)

        message_links = driver.find_elements(By.CSS_SELECTOR, "a.news-link")
        print(f"🔗 Found {len(message_links)} message links on page {page}")

        for i, link in enumerate(message_links):
            try:
                href = link.get_attribute("href")
                driver.execute_script("window.open(arguments[0]);", href)
                driver.switch_to.window(driver.window_handles[1])
                time.sleep(3)

                try:
                    title = driver.find_element(By.CSS_SELECTOR, "div.news-title > h1").text.strip()
                except:
                    title = "Unknown"

                try:
                    date = driver.find_element(By.CSS_SELECTOR, "div.news-date").text.strip()
                except:
                    date = None

                try:
                    summary = driver.find_element(By.CSS_SELECTOR, "div.article-content").text.strip()
                except:
                    summary = None

                message_data.append({
                    "title": title,
                    "date": date,
                    "url": href,
                    "summary": summary
                })

                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            except Exception as e:
                print(f"⚠️ Error processing message {i+1} on page {page}: {e}")
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

finally:
    driver.quit()

with open("usmc_messages.json", "w") as f:
    json.dump(message_data, f, indent=2)

print(f"✅ Saved {len(message_data)} messages to usmc_messages.json")
