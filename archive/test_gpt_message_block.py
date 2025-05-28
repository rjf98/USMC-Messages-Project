debug_mode = True
user_input = "Who won the award?"
message_bodies = "ALMAR 007/25\nCapt John Smith\n..."

if debug_mode:
    print(f"Debug: Selected message bodies:\n{message_bodies}")

# Phase 2: Answer the question using message bodies
try:
    model = "gpt-3.5-turbo-1106"
    messages = [
        {
            "role": "system",
            "content": "system_prompt_goes_here"
        },
        {
            "role": "user",
            "content": f"""
The user is asking a question. Use the full body content to answer like a Marine:
provide a brief, readable response — not JSON.
Use titles and plain language.

Question: {user_input}

Messages:

{message_bodies}
"""
        }
    ]
    print("✅ No syntax errors. Message block successfully constructed.")
except Exception as e:
    print("❌ Error:", e)
