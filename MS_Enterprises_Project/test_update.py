import requests
import json

res = requests.get('http://127.0.0.1:5000/api/admin/products')
products = res.json()
print(f'Total products: {len(products)}')
if products:
    p = products[0]
    print(f"Editing Product: {p.get('id')}, {p.get('name')}")
    
    # Try updating
    p['name'] = p.get('name') + " TEST"
    
    # Needs auth! Wait, the API has @login_required decorator.
    # To bypass it, we can use a test session cookie or just call the DB directly.
    # But we should test the API as the admin uses it.
