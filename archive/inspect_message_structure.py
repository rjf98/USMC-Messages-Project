# inspect_message_structure.py
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

# Print all divs with class names to inspect
divs = driver.find_elements("css selector", "div[class]")
print(f"Found {len(divs)} divs with class attributes.\n")

for div in divs[:25]:
    print("📦", div.get_attribute("class"))
    print("→", div.text[:120], "\n")

driver.quit()
