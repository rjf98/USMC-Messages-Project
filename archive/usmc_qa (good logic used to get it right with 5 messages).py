import json
import os
from datetime import datetime
from openai import OpenAI

# Load JSON messages
with open("usmc_messages.json", "r") as f:
    messages = json.load(f)

# Ask for OpenAI API key first
api_key = os.getenv("OPENAI_API_KEY") or input("Enter your OpenAI API key: ")
client = OpenAI(api_key=api_key)

# Summarize message statistics
dates = [datetime.strptime(m["date"], "%m/%d/%Y") for m in messages]
earliest = min(dates).strftime("%m/%d/%Y")
latest = max(dates).strftime("%m/%d/%Y")
counts = {"MARADMIN": 0, "ALMAR": 0, "UNKNOWN": 0}
for m in messages:
    cat = m.get("category", "UNKNOWN").upper()
    counts[cat if cat in counts else "UNKNOWN"] += 1

print(f"\n\U0001f4d2  There are {len(messages)} unique messages loaded.")
print(f"\U0001f4d3  Earliest: {earliest} | Latest: {latest}")
print(f"\U0001f5fe  Types: {counts['MARADMIN']} MARADMINs, {counts['ALMAR']} ALMARs, {counts['UNKNOWN']} Unknown\n")
print("Type 'exit' to quit.\n")

# Format full context string
def format_context(msgs):
    return "\n---\n".join(f"{m['category']} {m['number']}: {m['title']}\n{m['content']}" for m in msgs)

# Loop for Q&A
last_questions = []
while True:
    question = input("Enter your question: ").strip()
    if question.lower() in ["exit", "quit"]:
        break

    # Keep last 2 questions
    last_questions.append(question)
    last_questions = last_questions[-2:]

    print("[DEBUG] Sending prompt to GPT with full message context\n")

    context = format_context(messages)
    last_q_text = "\n\n".join(last_questions)

    system_prompt = (
        "You are an expert in Marine Corps administrative messages. "
        "Use your knowledge of Marine Corps terminology, acronyms, slang, rank structure, and doctrine to interpret questions naturally. "
        "You only have access to the MARADMIN and ALMAR messages provided. Do not reference outside data or make assumptions. "
        "Only answer using the provided message content. "
        "If asked how many messages you can access, reply based on the number of loaded messages. "
        "If the user follow-up is vague, try to clarify.\n\n"
        f"Here are the last two user questions: {last_q_text}\n\n"
        f"Here are the messages:\n\n{context}\n\n"
        f"Answer the question: {question}"
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt}
        ],
        temperature=0.3,
        max_tokens=1000
    )

    answer = response.choices[0].message.content.strip()

    # Try to guess the primary message used by looking for its number in the answer
    cited = next((m for m in messages if m.get("number") in answer), None)
    if cited:
        msg_type = cited.get("category", "UNKNOWN")
        msg_number = cited.get("number", "?")
        msg_date = cited.get("date", "Unknown Date")
        filename = cited.get("filename")

        citation = f"\n\n\U0001f4cc Source: {msg_type} {msg_number} — Signed {msg_date}"
        if filename:
            citation += f"\n\U0001f517 https://www.marines.mil/Portals/1/Publications/{filename}"
    else:
        citation = ""

    print("\n" + answer + citation + "\n")
