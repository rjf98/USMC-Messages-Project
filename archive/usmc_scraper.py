import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Setup headless browser
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
base_url = "https://www.marines.mil/News/Messages/?Page="

messages = []

def extract_message_data(detail_url):
    driver.get(detail_url)
    time.sleep(1)

    try:
        print_button = driver.find_element(By.LINK_TEXT, "Print")
        print_button.click()
        time.sleep(1)
        driver.switch_to.window(driver.window_handles[-1])
        content = driver.find_element(By.CSS_SELECTOR, "body").text
        url = driver.current_url
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return content, url
    except Exception as e:
        print(f"❌ Failed to extract message content: {e}")
        return None, None

page = 1
while True:
    print(f"Scraping page {page}...")
    driver.get(base_url + str(page))
    time.sleep(2)

    tiles = driver.find_elements(By.CLASS_NAME, "title")
    if not tiles:
        break

    for tile in tiles:
        try:
            title_element = tile.find_element(By.TAG_NAME, "a")
            title = title_element.text.strip()
            detail_url = title_element.get_attribute("href")

            number = "UNKNOWN"
            category = "UNKNOWN"
            date_str = "UNKNOWN"

            if "MARADMIN" in title.upper():
                category = "MARADMIN"
                number = title.upper().split("MARADMIN")[-1].strip().split()[0]
            elif "ALMAR" in title.upper():
                category = "ALMAR"
                number = title.upper().split("ALMAR")[-1].strip().split()[0]

            try:
                date_element = tile.find_element(By.XPATH, "../../..//div[@class='date']")
                date_str = date_element.text.strip()
            except NoSuchElementException:
                pass

            content, final_url = extract_message_data(detail_url)
            if content:
                messages.append({
                    "category": category,
                    "number": number,
                    "title": title,
                    "date": date_str,
                    "url": final_url,
                    "content": content
                })
        except Exception as e:
            print(f"❌ Error processing tile: {e}")

    page += 1
    if page > 100:
        break

driver.quit()

# Save to JSON
with open("usmc_messages.json", "w") as f:
    json.dump(messages, f, indent=2)

print(f"✅ Saved {len(messages)} messages to usmc_messages.json")
