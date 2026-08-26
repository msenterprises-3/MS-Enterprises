import requests
import json
import uuid
import time
from supabase_db import supabase_client

def update_bucket_to_public():
    try:
        # Try to update bucket to public
        supabase_client.storage.update_bucket('products', {'public': True})
    except Exception as e:
        print("Warning: could not update bucket to public:", e)

def main():
    update_bucket_to_public()
    
    print("Fetching products...")
    response = supabase_client.table('products').select('id, name, short_description, category_id').execute()
    products = response.data
    print(f"Found {len(products)} products.")

    for i, prod in enumerate(products):
        print(f"Processing {i+1}/{len(products)}: {prod['name']}")
        
        prompt = f"professional luxury e-commerce product photography of {prod['name']}, {prod['short_description']}, studio lighting, white background, highly detailed"
        # URL encode prompt
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
                
                # Update product
                supabase_client.table('products').update({'images': [public_url]}).eq('id', prod['id']).execute()
                print(f"  -> Uploaded and attached: {public_url}")
            else:
                print(f"  -> Failed to generate image, status: {img_resp.status_code}")
        except Exception as e:
            print(f"  -> Error: {e}")
            
        # Small delay to prevent rate limits
        time.sleep(1)
        
    print("All products processed!")

if __name__ == '__main__':
    main()
