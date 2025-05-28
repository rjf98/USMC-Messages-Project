import requests

url = "https://www.marines.mil/News/Messages/?Page=1"
headers = {
    "User-Agent": "Mozilla/5.0"
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    print("Status Code:", response.status_code)
    print("First 500 characters of response:")
    print(response.text[:500])
except Exception as e:
    print("❌ Error fetching page:", e)
