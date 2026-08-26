import requests
import json
import uuid
import time
import random
import urllib.parse
from supabase_db import supabase_client

def main():
    print("Fetching remaining products...")
    
    # Get all product images to know which products already have AI images
    img_res = supabase_client.table('product_images').select('product_id, image_url').execute()
    img_map = {}
    for img in img_res.data:
        pid = img['product_id']
        if pid not in img_map:
            img_map[pid] = []
        img_map[pid].append(img['image_url'])

    # Get all products
    response = supabase_client.table('products').select('id, name, short_description').execute()
    products = response.data

    remaining = []
    for p in products:
        images = img_map.get(p['id'], [])
        # Only process if there is no AI image
        if not any('.supabase.co' in img for img in images):
            remaining.append(p)

    print(f"Found {len(remaining)} products without AI images.")

    for i, prod in enumerate(remaining):
        print(f"[{i+1}/{len(remaining)}] Processing: {prod['name']}")
        
        desc = str(prod['short_description'] or '')
        prompt = f"Professional luxury e-commerce product photography of {prod['name']}, {desc}. White background, studio lighting, highly detailed, clean, focused"
        
        encoded_prompt = urllib.parse.quote(prompt)
        seed = random.randint(1, 100000)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=800&nologo=true&seed={seed}"
        
        success = False
        retries = 3
        while not success and retries > 0:
            try:
                img_resp = requests.get(url, timeout=45)
                if img_resp.status_code == 200:
                    img_data = img_resp.content
                    filename = f"prod_{prod['id']}_{uuid.uuid4().hex[:6]}.jpg"
                    
                    # Upload to Supabase Storage
                    supabase_client.storage.from_('products').upload(filename, img_data, {'content-type': 'image/jpeg'})
                    public_url = supabase_client.storage.from_('products').get_public_url(filename)
                    
                    # Check if an existing product_images entry exists and update it, else insert
                    existing = supabase_client.table('product_images').select('id').eq('product_id', prod['id']).execute()
                    
                    if existing.data:
                        # Update first entry
                        img_id = existing.data[0]['id']
                        supabase_client.table('product_images').update({'image_url': public_url}).eq('id', img_id).execute()
                        
                        # Delete any extra old entries for the same product to clean up
                        for extra in existing.data[1:]:
                            supabase_client.table('product_images').delete().eq('id', extra['id']).execute()
                    else:
                        # Insert
                        max_id_res = supabase_client.table('product_images').select('id').order('id', desc=True).limit(1).execute()
                        new_id = (max_id_res.data[0]['id'] + 1) if max_id_res.data else 1
                        supabase_client.table('product_images').insert({'id': new_id, 'product_id': prod['id'], 'image_url': public_url, 'display_order': 0}).execute()
                        
                    print(f"  -> Uploaded and attached: {public_url}")
                    success = True
                    time.sleep(5)  # Delay to respect limits
                elif img_resp.status_code == 429:
                    print(f"  -> Rate limited (429), retrying in 20 seconds... ({retries} left)")
                    time.sleep(20)
                    retries -= 1
                else:
                    print(f"  -> Failed, status: {img_resp.status_code}")
                    break
            except Exception as e:
                print(f"  -> Error: {e}")
                time.sleep(10)
                retries -= 1
                
    print("All products processed!")

if __name__ == '__main__':
    main()
