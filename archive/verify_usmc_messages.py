import json

with open("usmc_messages.json", "r") as f:
    messages = json.load(f)

for i, msg in enumerate(messages[:5]):
    print(f"\n🔹 Message {i + 1}")
    print(f"Title: {msg.get('title')}")
    print(f"Date: {msg.get('date')}")
    print(f"URL: {msg.get('url')}")
    summary = msg.get('summary') or ""
    print(f"Summary: {summary[:200]}...")  # Truncated preview
