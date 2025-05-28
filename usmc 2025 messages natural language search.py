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
1. Interpret the question
2. Return the top 10 most likely message numbers (e.g., ["MARADMIN 123/25", "ALMAR 004/25"])
3. If the user asks for 'all' of a type, assume they want every match.
4. If the question is unclear, ask a clarifying follow-up.

Do not answer the question yet. Just return the list of message numbers that might help.
Return ONLY a valid JSON array of message numbers. Do not explain or describe anything else.
"""

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

    try:
        content = response.choices[0].message.content.strip()
        suggested = json.loads(content)
    except Exception as e:
        print(f"❌ GPT response unreadable: {e}")
        print("Raw output:\n", content)
        continue

    # Phase 2 — pull full messages and ask again
    full_prompt = "Here is the full content of the selected messages. Answer the user's question directly. " \
    "Answer the users question using the context of the messages. Always respond in complete sentences." \
    "Be as helpful and concise as possible. If unsure, ask 1–2 clarifying follow-ups. If still unsure, say " \
    "'sorry, don't understand.' When you answer always include the following at the end of your answer:" \
    "Message number (e.g, MARADMIN 246/25)\n" \
    "Title (e.g, 'New Policy on Leave')\n" \
    "Signed date (e.g, 2025-06-15)\n" \
    "URL (e.g, https://www.marines.mil/News/Messages/ALMAR/2025/ALMAR-004-25)\n" \

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
        model="gpt-4",
        messages=[
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": f"User question: {user_input}\n\nMessages:\n\n" + "\n\n".join(full_messages)}
        ],
        temperature=0.4
    )

    print("\n🧠 GPT Answer:\n")
    print(answer.choices[0].message.content.strip())
    print("\n---")
