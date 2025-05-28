response = {
    "role": "user",
    "content": f"""
The user is asking a question. Use the full body content to answer like a Marine:
provide a brief, readable response — not JSON.
Use titles and plain language.

Question: {{user_input}}

Messages:

{{message_bodies}}
"""
}

print("✅ Successfully parsed the f-string block.")
print("Content Preview:")
print(response["content"])
