import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# File paths
MASTER_JSON = "/Volumes/1TB SSD/usmc_project/usmc_2025_message_links.json"

# Load existing messages
try:
    with open(MASTER_JSON) as f:
        known = json.load(f)
        seen_urls = set(msg["url"] for msg in known)
except FileNotFoundError:
    known = []
    seen_urls = set()

# Set up headless browser
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 10)

base_url = "https://www.marines.mil/News/Messages/?Page=1"
new_messages = []

try:
    page = 1
    keep_checking = True
    while keep_checking:
        driver.get(f"https://www.marines.mil/News/Messages/?Page={page}")
        time.sleep(5)

        links = driver.find_elements(By.CSS_SELECTOR, "a.news-link")
        seen_hrefs = set()
        message_refs = []
        for el in links:
            href = el.get_attribute("href")
            if href and href not in seen_hrefs:
                seen_hrefs.add(href)
                message_refs.append({
                    "href": href,
                    "title": el.text.strip()
                })

        for ref in message_refs:
            href = ref["href"]
            if href in seen_urls:
                print(f"🛑 Found existing message at {href}. Stopping.")
                keep_checking = False
                break

            try:
                driver.get(href)
                time.sleep(3)
                print_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href*="Print.aspx"]')))
                print_button.send_keys(Keys.RETURN)
                time.sleep(5)

                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(2)

                try:
                    try:
                        content = driver.find_element(By.CSS_SELECTOR, ".cs-article-body").text.strip()
                    except:
                        content = driver.find_element(By.TAG_NAME, "body").text.strip()

                    if "2025" not in content:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        continue

                    title_line = content.splitlines()[0].strip().rstrip("\\")

                    new_msg = {
                        "title": title_line,
                        "url": href,
                        "date": "2025",
                        "content": content
                    }

                    print(f"✅ New message: {title_line}")
                    new_messages.append(new_msg)

                finally:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    time.sleep(1)

            except Exception as e:
                print(f"⚠️ Failed to process {href}: {e}")

finally:
        page += 1

driver.quit()

if new_messages:
    known.extend(new_messages)
    with open(MASTER_JSON, "w") as f:
        json.dump(known, f, indent=2)
    print(f"✅ Added {len(new_messages)} new messages to master file.")
else:
    print("🔎 No new messages found.")
