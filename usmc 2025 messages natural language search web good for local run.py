import json
import os
from flask import Flask, request, render_template_string
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

SUMMARY_FILE = "/Volumes/1TB SSD/usmc_project/usmc_messages_2025_summary.json"
ENRICHED_FILE = "/Volumes/1TB SSD/usmc_project/usmc_messages_2025_enriched.json"

with open(SUMMARY_FILE) as f:
    summaries = json.load(f)

with open(ENRICHED_FILE) as f:
    enriched = json.load(f)

message_index = {m["message_number"]: m for m in enriched if m.get("message_number")}

system_prompt = """
You are a Marine responding to Marines. You are an expert at Marine administrative messages. Use all of your knowledge of Marine Corps terminology, acronyms, slang, rank structure, and doctrine to interpret questions naturally.

You will be passed a list of message summaries and a user question.

Your job is to:
1. Interpret the question.
2. If the user's input is ambiguous or short, assume it may be a follow-up. Ask: "Is this a follow-up to the previous message?" If yes, keep using the last selected message(s). If no, return to searching across all messages.
3. Return a JSON array of all relevant message numbers. Include as many as are clearly related to the question.
4. If the user asks for "all" of a type (e.g., all award messages or all assignment messages), include every matching message number.
5. If the user is asking broadly (e.g., "what awards were given out this year" or "what messages are about awards"), do not limit to only a few matches — return all that clearly relate to awards. Err on the side of inclusion and do not assume the user only wants a summary or one result.
5a. If the user asks a broad question like "what messages do you have about awards," return a complete list of all relevant messages, not just the top one. Use multiple entries in the returned JSON array if necessary.
6. If the user's question includes specific domain keywords (e.g., "aviation", "legal", "logistics", "intel", "communications"), prioritize any messages that include those words 
in their titles. Score these higher and do not ignore them even if other messages are more general.
7. If the question appears to be a follow-up to the last one, answer it using only the current messages.
8. Otherwise, search again using summaries. Respond using only the selected messages.
9. If the user appears to be asking for a list of messages (e.g., "What messages are about promotions?"), return only a JSON array of message numbers, as in ["MARADMIN 123/25", "MARADMIN 124/25"]. Do not summarize the messages or provide commentary before the array.

Do not answer the question yet. Return ONLY a valid JSON array of message numbers. 
You must return a list like ["MARADMIN 123/25", "MARADMIN 165/25"]. Do not explain your choices. 
Do not return markdown, bullet points, or anything else — only the JSON array.
"""

full_prompt = (
    "You are a Marine responding to another Marine. Based on the full content of the selected messages, "
    "answer the user's question clearly and accurately. If you are unsure, ask up to 2 clarifying questions. "
    "If still unclear, respond with 'Sorry, I don't understand. Try asking another way.' "
    "If the user's question is asking for a list of messages, return the full list as individual entries using numbered bullet points, followed by structured output in JSON format. "
    "Always respond in complete sentences. Use the message content to extract specific names, winners, or units when asked. "
    "Return a JSON object with the following fields:\n"
    "- answer (string): your written answer to the user's question. Format this answer for readability:\n"
    "  - Use numbered bullet points if referencing multiple messages. Example:\n"
    "    1. MARADMIN 123/25 covers...\n"
    "    2. MARADMIN 124/25 discusses...\n"
    "  - If referencing multiple individuals, groups, or award recipients (e.g., Male, Female, and Team of the Year), use a cleanly formatted list or paragraph breaks to separate them.\n"
    "  - When appropriate, use clearly structured formatting like indented bullet points or tables to distinguish between recipients and their achievements.\n"
    "  - Keep each bullet brief but complete.\n"
    "  - Avoid markdown formatting (like backticks or asterisks). Write in plain text for clean display in HTML.\n"
    "- message_number (string or list of strings): If multiple messages are used, return a list such as [\"MARADMIN 123/25\", \"MARADMIN 124/25\"]\n"
    "- title (string or list of strings): Matching list of full titles\n"
    "- signed_date (string or list of strings): Matching list of signed dates\n"
    "- url (string or list of strings): Matching list of URLs\n"
    "\n"
    "Display messages in the order they are referenced in the answer. This helps the UI render links, titles, and dates clearly.\n"
    "\n"
    "Avoid extra commentary, markdown, or prose outside the expected fields."
)

app = Flask(__name__)
last_messages = []

TEMPLATE = """
<!doctype html>
<title>USMC Message Q&A</title>
<h2>Ask a question about USMC Messages (2025)</h2>
<form method=post>
  <textarea name=question rows=4 cols=100 placeholder="Type your question here...">{{ question or '' }}</textarea><br><br>
  <input type=submit value="Submit">
</form>
{% if response %}
<hr>
<h3>Response:</h3>
<div>{{ response|safe }}</div>
{% endif %}
<script>
  const textarea = document.querySelector("textarea[name='question']");
  textarea.addEventListener("keydown", function(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      this.form.submit();
      setTimeout(() => { textarea.focus(); }, 50);
    }
  });
  window.onload = function() {
    textarea.focus();
  };
</script>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    global last_messages
    question = None
    response_text = None

    if request.method == "POST":
        question = request.form["question"]

        summary_text = json.dumps(summaries[:100], indent=2)

        try:
            phase1 = client.chat.completions.create(
                model="gpt-4-turbo-2024-04-09",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f'User question: "{question}"\n\nHere is a JSON array of message summaries:\n\n{summary_text}'}
                ],
                temperature=0
            )
        except openai.RateLimitError:
            response_text = "⚠️ Rate limit or quota exceeded during initial GPT call. Please check your OpenAI usage or try again shortly."
            question = ""
            return render_template_string(TEMPLATE, question=question, response=response_text)

        content = phase1.choices[0].message.content.strip()

        try:
            suggested = json.loads(content)
            def normalize(n):
                if isinstance(n, int):
                    return f"MARADMIN {n}/25"
                elif isinstance(n, str) and n.strip().isdigit():
                    return f"MARADMIN {n.strip()}/25"
                return n.strip().upper()
            suggested = [normalize(n) for n in suggested]
        except json.JSONDecodeError:
            import re
            matches = re.findall(r"(MARADMIN|ALMAR) ?\d{3}/25", content.upper())
            if matches:
                suggested = list(set(matches))
            else:
                response_text = "⚠️ GPT response could not be parsed. Try rephrasing your question."
                question = ""
                return render_template_string(TEMPLATE, question=question, response=response_text)

        last_messages = suggested[:10]
        full_messages = []
        for msgnum in last_messages:
            msg = message_index.get(msgnum)
            if msg:
                full_messages.append(
                    f'{msg["message_number"]}\nTitle: {msg["title"]}\nSigned date: {msg["signed_date"]}\nURL: {msg["url"]}\n\n{msg["content"]}\n---'
                )

        if not full_messages:
            response_text = f"⚠️ No matching messages found. GPT suggested: {last_messages}"
            question = ""
        else:
            try:
                phase2 = client.chat.completions.create(
                    model="gpt-4-turbo-2024-04-09",
                    messages=[
                        {"role": "system", "content": full_prompt},
                        {"role": "user", "content": f"User question: {question}\n\nMessages:\n\n" + "\n\n".join(full_messages)}
                    ],
                    temperature=0.4
                )
            except openai.RateLimitError:
                response_text = "⚠️ Rate limit or quota exceeded during message answering. Please check your OpenAI usage or try again shortly."
                question = ""
                return render_template_string(TEMPLATE, question=question, response=response_text)
            import html
            import re
            try:
                gpt_raw = phase2.choices[0].message.content.strip()
                # Try to extract a JSON block from a GPT response that may be inside triple backticks
                import re
                json_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", gpt_raw, re.DOTALL)
                if json_block_match:
                    json_string = json_block_match.group(1)
                else:
                    # Fallback: try to find any JSON object at the end of the message
                    json_fallback_match = re.search(r"(\{.*\})\s*$", gpt_raw, re.DOTALL)
                    if json_fallback_match:
                        json_string = json_fallback_match.group(1)
                    else:
                        raise ValueError("No JSON object found in GPT response.")
                gpt_response = json.loads(json_string)
                if isinstance(gpt_response, dict) and isinstance(gpt_response.get("answer"), list):
                    gpt_response["answer"] = "\n".join(item for item in gpt_response["answer"])
                if isinstance(gpt_response, list):
                    blocks = []
                    for item in gpt_response:
                        blocks.append(
                            f"<p>{html.escape(item['answer'])}</p>"
                            f"<p><strong><a href='{item['url']}' target='_blank'>{item['message_number']}</a></strong><br>"
                            f"Title: {html.escape(item['title'])}<br>"
                            f"Signed date: {html.escape(item['signed_date'])}</p><hr>"
                        )
                    response_text = "\n".join(blocks)
                else:
                    # Check if this is a JSON object with lists as fields
                    if isinstance(gpt_response.get("message_number"), list):
                        answer_html = "<ol>" + "".join(f"<li>{html.escape(line.strip())}</li>" for line in gpt_response["answer"].split("\n") if line.strip()) + "</ol>"
                        response_lines = [answer_html]
                        for i in range(len(gpt_response["message_number"])):
                            num = gpt_response["message_number"][i]
                            title = gpt_response["title"][i]
                            date = gpt_response["signed_date"][i]
                            url = gpt_response["url"][i]
                            response_lines.append(
                                f"<p><strong><a href='{url}' target='_blank'>{num}</a></strong><br>"
                                f"Title: {html.escape(title)}<br>"
                                f"Signed date: {html.escape(date)}</p><hr>"
                            )
                        response_text = "\n".join(response_lines)
                    else:
                        response_text = (
                            f"<p>{html.escape(gpt_response['answer'])}</p>"
                            f"<p><strong><a href='{gpt_response['url']}' target='_blank'>{gpt_response['message_number']}</a></strong><br>"
                            f"Title: {html.escape(gpt_response['title'])}<br>"
                            f"Signed date: {html.escape(gpt_response['signed_date'])}</p>"
                        )
            except Exception as e:
                response_text = f"⚠️ Failed to parse GPT response: {e}<br><br>Raw output:<br><pre>{phase2.choices[0].message.content.strip()}</pre>"
            question = ""

    return render_template_string(TEMPLATE, question=question, response=response_text)

if __name__ == "__main__":
    app.run(debug=True)
