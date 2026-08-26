import sys
import uuid
import os
from supabase_db import supabase_client

def upload_and_update(product_id, image_path):
    if not os.path.exists(image_path):
        print(f"Error: Image {image_path} not found.")
        return
        
    with open(image_path, 'rb') as f:
        img_data = f.read()
        
    filename = f"prod_{product_id}_{uuid.uuid4().hex[:6]}.jpg"
    
    try:
        supabase_client.storage.from_('products').upload(filename, img_data, {'content-type': 'image/jpeg'})
        public_url = supabase_client.storage.from_('products').get_public_url(filename)
        
        # Upsert into product_images
        existing = supabase_client.table('product_images').select('id').eq('product_id', product_id).execute()
        if existing.data:
            img_id = existing.data[0]['id']
            supabase_client.table('product_images').update({'image_url': public_url}).eq('id', img_id).execute()
        else:
            max_id_res = supabase_client.table('product_images').select('id').order('id', desc=True).limit(1).execute()
            new_id = (max_id_res.data[0]['id'] + 1) if max_id_res.data else 1
            supabase_client.table('product_images').insert({'id': new_id, 'product_id': product_id, 'image_url': public_url, 'display_order': 0}).execute()
            
        print(f"Successfully uploaded and linked image for product {product_id}: {public_url}")
    except Exception as e:
        print(f"Failed to upload image for product {product_id}: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python upload_generated_image.py <product_id> <image_path>")
        sys.exit(1)
    
    product_id = sys.argv[1]
    image_path = sys.argv[2]
    upload_and_update(product_id, image_path)
