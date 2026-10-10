with open('frontend/js/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix XSS rendering
text = text.replace("m.role === 'assistant' ? m.content : ui.esc(m.content)", "ui.esc(m.content)")

# Fix CSRF fetch
text = text.replace("headers: { 'Content-Type': 'application/json' }", "headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }")

with open('frontend/js/app.js', 'w', encoding='utf-8') as f:
    f.write(text)
