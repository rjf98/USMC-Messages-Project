# test_message_page_load.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)
driver.get("https://www.marines.mil/News/Messages/")
time.sleep(5)

print("✅ Page title:", driver.title)
print("✅ Page URL:", driver.current_url)

# Try to grab all message cards
elements = driver.find_elements("css selector", ".card-title")
print(f"✅ Found {len(elements)} message titles.")

for el in elements[:5]:  # print first 5 to preview
    print("•", el.text)

driver.quit()
