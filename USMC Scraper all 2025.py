import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException, NoSuchWindowException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Set up Chrome options
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Initialize the driver
try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
except WebDriverException as e:
    print(f"❌ Failed to start Chrome: {e}")
    exit(1)

wait = WebDriverWait(driver, 10)
base_url = "https://www.marines.mil/News/Messages/?Page={}"
message_data = []

try:
    page = 1
    keep_scraping = True
    while keep_scraping:
        print(f"🌐 Scraping page {page}...")
        driver.get(base_url.format(page))
        time.sleep(10 if page == 1 else 5)

        raw_links = driver.find_elements(By.CSS_SELECTOR, "a.news-link")

        seen_hrefs = set()
        message_refs = []
        for el in raw_links:
            href = el.get_attribute("href")
            if href and href not in seen_hrefs:
                seen_hrefs.add(href)
                message_refs.append({
                    "href": href,
                    "title": el.text.strip()
                })

        if not message_refs:
            print("❌ No more messages found. Stopping.")
            break

        print(f"🔗 Found {len(message_refs)} links on page {page}.")

        for ref in message_refs:
            href = ref["href"]
            title = ref["title"]

            print(f"➡️ Clicking into message: {title}")

            try:
                link = driver.find_element(By.XPATH, f'//a[@href="{href}"]')
                link.click()
                time.sleep(5)

                print("🖨️ Waiting for Print button...")
                print_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href*="Print.aspx"]')))
                print_button.send_keys(Keys.RETURN)
                time.sleep(5)

                print("🧭 Switching to print view tab...")
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(3)

                print("📄 Extracting message content and metadata...")
                try:
                    try:
                        content = driver.find_element(By.CSS_SELECTOR, ".cs-article-body").text.strip()
                    except:
                        print("⚠️ .cs-article-body not found. Falling back to full page body.")
                        content = driver.find_element(By.TAG_NAME, "body").text.strip()

                    should_save = False
                    if "2025" in content:
                        print("✅ Found 2025 in content. Saving message.")
                        should_save = True
                    elif "2024" in content:
                        print("🛑 Found 2024 in content before 2025. Stopping scrape.")
                        keep_scraping = False
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        break
                    else:
                        print("⚠️ No clear year found in content. Skipping.")
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        continue

                    # Extract first line as title
                    title_line = content.splitlines()[0].strip().rstrip("\\")

                    if any(entry['url'] == href for entry in message_data):
                        print("⚠️ Duplicate message detected. Skipping.")
                    elif should_save:
                        print(f"✅ Saved: {title_line} | 2025")
                        message_data.append({
                            "title": title_line,
                            "url": href,
                            "date": "2025",
                            "content": content
                        })

                        output_path = "/Volumes/1TB SSD/usmc_project/usmc_2025_message_links.json"
                        with open(output_path, "w") as f:
                            json.dump(message_data, f, indent=2)

                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    driver.back()
                    time.sleep(3)

                except Exception as e:
                    print(f"⚠️ Could not process message at {title or href}: {e}")
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    driver.back()
                    time.sleep(3)

            except Exception as outer_e:
                print(f"⚠️ Unexpected error at {href}: {outer_e}")
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                continue

        page += 1

finally:
    driver.quit()

print(f"✅ Finished. Collected {len(message_data)} messages.")
