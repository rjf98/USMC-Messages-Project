def test():
    message = f"""The user is asking a question. Use the full body content to answer like a Marine:
provide a brief, readable response — not JSON.
Use titles and plain language.

Question: {{user_input}}

Messages:

{{message_bodies}}
"""
    print(message)

test()
