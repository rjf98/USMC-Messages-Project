
import json
from datetime import datetime
from collections import Counter
import openai
from getpass import getpass

# Prompt for OpenAI API key immediately and securely
api_key = getpass("🔑 Enter your OpenAI API key: ").strip()
client = openai.OpenAI(api_key=api_key)

# Load messages
with open("usmc_messages_enriched.json", "r") as f:
    messages = json.load(f)

# Restore message stats
type_counter = Counter()
dates = []

for m in messages:
    number = m.get("message_number") or ""
    if number.startswith("MARADMIN"):
        type_counter["MARADMIN"] += 1
    elif number.startswith("ALMAR"):
        type_counter["ALMAR"] += 1
    else:
        type_counter["Other"] += 1

    date = m.get("date")
    if date and isinstance(date, str):
        try:
            dates.append(date)
        except Exception:
            pass

print(f"\n📄 Loaded {len(messages)} messages")
print(f"🧾 MARADMINs: {type_counter['MARADMIN']}, ALMARs: {type_counter['ALMAR']}, Other: {type_counter['Other']}")
if dates:
    print(f"📆 Date range: {min(dates)} to {max(dates)}")
print("Type your question or type 'exit' to quit.\n")

# Chat loop
while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ["exit", "quit"]:
        print("Goodbye!")
        break

    if user_input.lower() in ["list", "list all", "list messages"]:
        for m in messages:
            print(f"- {m.get('message_number') or '[Unknown]'}: {m['title']}")
        continue

    # Ask GPT with context
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert in Marine Corps administrative messages. Use your knowledge of Marine Corps "
                    "terminology, acronyms, slang, rank structure, and doctrine to interpret questions naturally. You only "
                    "have access to the messages provided in the context below. Do not reference outside data or make assumptions. "
                    "Only answer using the provided message content. If the user follow-up is vague, try to clarify."
                )
            },
            {
                "role": "user",
                "content": user_input + "\n\nMessages:\n" + json.dumps(messages[-60:], indent=2)
            }
        ],
        temperature=0.2
    )

    print("\n🧠 Answer:")
    print(response.choices[0].message.content.strip())
