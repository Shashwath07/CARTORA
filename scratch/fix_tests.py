with open('tests/test_concurrency.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("return s.post(f'{BASE_URL}/api/orders/demo-checkout', json={'product_id': 'P1005'})", "return s.post(f'{BASE_URL}/api/orders/demo-checkout', json={'product_id': 'P1005'}, headers={'X-Requested-With': 'XMLHttpRequest'})")

with open('tests/test_concurrency.py', 'w', encoding='utf-8') as f:
    f.write(text)
