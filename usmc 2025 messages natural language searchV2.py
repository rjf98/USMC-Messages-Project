import json
import os
from openai import OpenAI
client = OpenAI()  # Uses OPENAI_API_KEY from environment

SUMMARY_FILE = "/Volumes/1TB SSD/usmc_project/usmc_messages_2025_summary.json"
ENRICHED_FILE = "/Volumes/1TB SSD/usmc_project/usmc_messages_2025_enriched.json"

with open(SUMMARY_FILE) as f:
    summaries = json.load(f)

with open(ENRICHED_FILE) as f:
    enriched = json.load(f)

# Index enriched messages by message_number for lookup
index = {m["message_number"]: m for m in enriched if m.get("message_number")}

# Count by type
type_counts = {}
for msg in enriched:
    t = msg.get("message_type")
    if t:
        type_counts[t] = type_counts.get(t, 0) + 1

print(f"📄 Loaded {len(enriched)} messages")
for k, v in type_counts.items():
    print(f"🧾 {k}s: {v}")

system_prompt = """
You are a Marine responding to Marines. You are an expert at Marine administrative messages. Use all of your knowledge of Marine Corps terminology, acronyms, slang, rank structure, and doctrine to interpret questions naturally.

You will be passed a list of message summaries and a user question.

Your job is to:
1. Interpret the question.
2. If the user's input is ambiguous or short, assume it may be a follow-up. Ask: 'Is this a follow-up to the previous message?' If yes, keep using the last selected message(s). If no, return to searching across all messages.
3. Return the top 10 most likely message numbers (e.g., ["MARADMIN 123/25", "ALMAR 004/25"])
4. If the user asks for 'all' of a type, assume they want every match.

Do not answer the question yet. Return ONLY a valid JSON array of message numbers. Do not explain or include anything else.
"""

last_messages = []

while True:
    user_input = input("You: ").strip()
    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    summary_text = "\n".join([
        f"{m['message_number']} | {m['title']} | {m['signed_date']}"
        for m in summaries if m.get("message_number") and m.get("title")
    ])

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User question: {user_input}\n\nHere are the message summaries:\n{summary_text}"}
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()

    try:
        suggested = json.loads(content)
    except json.JSONDecodeError:
        print("❌ GPT response was not a JSON list.")
        print("🧠 GPT replied:", content)
        user_followup = input("Is this a follow-up to the previous message? (y/n): ").strip().lower()
        if user_followup == "y" and last_messages:
            suggested = last_messages
        else:
            print("🔁 Restarting with full search...")
            continue

    last_messages = suggested[:10]

    full_prompt = (
        "You are a Marine responding to another Marine. Based on the full content of the selected messages, "
        "answer the user's question clearly and accurately. If you are unsure, ask up to 2 clarifying questions. "
        "If still unclear, respond with 'Sorry, I don't understand. Try asking another way.'\n\n"
        "Always respond in complete sentences.\n\n"
        "Include the following in your final response:\n"
        "- Message number (e.g., MARADMIN 246/25)\n"
        "- Title\n"
        "- Signed date\n"
        "- A hyperlink to the message\n"
    )

    full_messages = []
    for msgnum in suggested[:10]:
        msg = index.get(msgnum)
        if msg:
            full_messages.append(
                f"{msg['message_number']} | {msg['title']} | {msg['signed_date']} | {msg['url']}\n{msg['content']}\n---"
            )

    if not full_messages:
        print("⚠️ No matching messages found. Try a different query.")
        continue

    answer = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": f"User question: {user_input}\n\nMessages:\n\n" + "\n\n".join(full_messages)}
        ],
        temperature=0.4
    )

    print("\n🧠 GPT Answer:\n")
    print(answer.choices[0].message.content.strip())
    print("\n---")