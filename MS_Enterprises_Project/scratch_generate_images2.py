import requests
import json
import uuid
import time
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
    print(f"Found {len(products)} products.")

    for i, prod in enumerate(products):
        print(f"Processing {i+1}/{len(products)}: {prod['name']}")
        
        desc = str(prod['short_description'] or '')
        prompt = f"professional luxury e-commerce product photography of {prod['name']}, {desc}, studio lighting, white background, highly detailed"
        
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=800&nologo=true"
        
        try:
            img_resp = requests.get(url, timeout=30)
            if img_resp.status_code == 200:
                img_data = img_resp.content
                
                filename = f"prod_{prod['id']}_{uuid.uuid4().hex[:6]}.jpg"
                
                # Upload to Supabase
                supabase_client.storage.from_('products').upload(filename, img_data, {'content-type': 'image/jpeg'})
                
                # Get URL
                public_url = supabase_client.storage.from_('products').get_public_url(filename)
                
                # Upsert into product_images
                # check existing
                existing = supabase_client.table('product_images').select('id').eq('product_id', prod['id']).execute()
                if existing.data:
                    img_id = existing.data[0]['id']
                    supabase_client.table('product_images').update({'image_url': public_url}).eq('id', img_id).execute()
                else:
                    # We need a new id, query max id
                    max_id_res = supabase_client.table('product_images').select('id').order('id', desc=True).limit(1).execute()
                    new_id = (max_id_res.data[0]['id'] + 1) if max_id_res.data else 1
                    supabase_client.table('product_images').insert({'id': new_id, 'product_id': prod['id'], 'image_url': public_url, 'display_order': 0}).execute()
                    
                print(f"  -> Uploaded and attached: {public_url}")
            else:
                print(f"  -> Failed to generate image, status: {img_resp.status_code}")
        except Exception as e:
            print(f"  -> Error: {e}")
            
        # Small delay
        time.sleep(1)
        
    print("All products processed!")

if __name__ == '__main__':
    main()
