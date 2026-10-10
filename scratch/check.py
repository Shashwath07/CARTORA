with open('frontend/js/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print('assistant usages:', len(re.findall(r"m\.role === 'assistant'", text)))
