import json
import re
import openai
from getpass import getpass
from collections import Counter

# Load cleaned messages
with open("usmc_messages_cleaned.json", "r") as f:
    messages = json.load(f)

# Count message types
type_counter = Counter()
for m in messages:
    msg = (m.get("message_number") or "").upper()
    if msg.startswith("MARADMIN"):
        type_counter["MARADMIN"] += 1
    elif msg.startswith("ALMAR"):
        type_counter["ALMAR"] += 1
    else:
        type_counter["Other"] += 1

# Prompt for API key and debug mode
api_key = getpass("🔑 Enter your OpenAI API key: ").strip()
client = openai.OpenAI(api_key=api_key)
debug_mode = input("🛠 Debug mode? (y/n): ").strip().lower().startswith("y")

# Prepare message index for display and ranking
index = []
for m in messages:
    msg_num = m.get("message_number") or "[Unknown]"
    title = m.get("title") or "[Untitled]"
    index.append(f"{msg_num}: {title}")

print(f"📄 Loaded {len(messages)} messages")
print(f"🧾 MARADMINs: {type_counter['MARADMIN']}, ALMARs: {type_counter['ALMAR']}, Other: {type_counter['Other']}")
print("Type your search question or type 'exit' to quit.\n")

# Normalize message numbers for matching
def normalize(n):
    try:
        n = n.upper().replace("MARADMIN", "MARADMIN ").replace("ALMAR", "ALMAR ").strip()
        if " " in n:
            prefix, val = n.split(" ")
            if "/" in val:
                num, year = val.split("/")
                return f"{prefix} {int(num)}/{year}"
    except:
        pass
    return n.strip().upper()

# System instruction for GPT
system_prompt = """You are a Marine responding to Marines. Utilize all of your knowledge of Marine Corps history, jargon, slang, orders, order of battle, units, etc. to assist you in understanding what your fellow Marine is asking you to do.

Initially, you will only be passed numbers and titles of messages. When the user asks you a question, query those to see which messages are relevant to the question based on the title. If the user asks for 'all' of a type, assume they want every match.

Respond ONLY with a JSON list of the message numbers you want to review in full (e.g., ["MARADMIN 123/24", "ALMAR 005/25"]). Do not explain or include any other text.

Once you have determined the messages you want to see, you will receive the full message body. Use it to answer the question directly.

If the user is asking for a list of messages, respond with message numbers and titles in natural language. Do not return raw JSON unless explicitly asked. Always prefer readable output formatted like a brief."""

# Interaction loop
while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ["exit", "quit"]:
        print("Goodbye!")
        break

    # Phase 1: Ask GPT to select messages by title
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "User question: " + user_input + "\n\nHere are the message titles:\n" + "\n".join(index)}
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("```")[-2].strip()
    match = re.search(r"\[\s*\"(MARADMIN|ALMAR).*?\]", content, re.DOTALL)
    if match:
        content = match.group(0)

    try:
        ranked = json.loads(content)
        ranked_set = set(normalize(x) for x in ranked)
    except Exception:
        print("⚠️ Failed to parse GPT response.")
        print(response.choices[0].message.content)
        continue

    relevant_messages = [
        m for m in messages
        if normalize(m.get("message_number") or "") in ranked_set
    ]

    if not relevant_messages:
        print("🤔 No matching messages found.")
        continue

    print(f"🔍 GPT selected {len(relevant_messages)} messages. Asking full question...")
    if debug_mode:
        print("\n📋 Suggested messages:")
        for m in relevant_messages:
            print(f" - {m.get('message_number')}: {m.get('title')}")

    # Build message body string separately
    message_bodies = "\n".join([f"{m['message_number']}:\n{m['body']}" for m in relevant_messages])

    # Phase 2: Ask GPT to answer using message bodies
    response2 = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"""The user is asking a question. You have already selected the messages you need.
Use their full body content to answer like a Marine: provide a brief, readable response — not JSON.
Use titles and plain language.

Question: {user_input}

Messages:

{message_bodies}
"""
            }
        ],
        temperature=0.3
    )

    print("\n🧠 Answer:")
    print(response2.choices[0].message.content.strip())
