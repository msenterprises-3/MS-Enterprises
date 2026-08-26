import requests
import json
import uuid
import time
import random
from supabase_db import supabase_client

def update_bucket_to_public():
    try:
        supabase_client.storage.update_bucket('products', {'public': True})
    except Exception as e:
        pass

def main():
    update_bucket_to_public()
    
    print("Fetching products...")
    response = supabase_client.table('products').select('id, name, short_description, category_id').execute()
    products = response.data
    
    # We only process products that don't already have an image in product_images
    existing_imgs = supabase_client.table('product_images').select('product_id').execute()
    existing_ids = {str(r['product_id']) for r in existing_imgs.data}
    
    products = [p for p in products if str(p['id']) not in existing_ids]
    print(f"Found {len(products)} products without images.")

    for i, prod in enumerate(products):
        print(f"Processing {i+1}/{len(products)}: {prod['name']}")
        
        desc = str(prod['short_description'] or '')
        prompt = f"professional luxury e-commerce product photography of {prod['name']}, {desc}, studio lighting, white background, highly detailed"
        
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        seed = random.randint(1, 100000)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=800&nologo=true&seed={seed}"
        
        success = False
        retries = 5
        while not success and retries > 0:
            try:
                img_resp = requests.get(url, timeout=30)
                if img_resp.status_code == 200:
                    img_data = img_resp.content
                    filename = f"prod_{prod['id']}_{uuid.uuid4().hex[:6]}.jpg"
                    
                    supabase_client.storage.from_('products').upload(filename, img_data, {'content-type': 'image/jpeg'})
                    public_url = supabase_client.storage.from_('products').get_public_url(filename)
                    
                    max_id_res = supabase_client.table('product_images').select('id').order('id', desc=True).limit(1).execute()
                    new_id = (max_id_res.data[0]['id'] + 1) if max_id_res.data else 1
                    supabase_client.table('product_images').insert({'id': new_id, 'product_id': prod['id'], 'image_url': public_url, 'display_order': 0}).execute()
                        
                    print(f"  -> Uploaded and attached: {public_url}")
                    success = True
                    time.sleep(3) # Base delay to respect limits
                elif img_resp.status_code == 429:
                    print(f"  -> Rate limited, retrying in 15 seconds... ({retries} left)")
                    time.sleep(15)
                    retries -= 1
                else:
                    print(f"  -> Failed, status: {img_resp.status_code}")
                    break
            except Exception as e:
                print(f"  -> Error: {e}")
                time.sleep(5)
                retries -= 1
                
    print("All products processed!")

if __name__ == '__main__':
    main()
