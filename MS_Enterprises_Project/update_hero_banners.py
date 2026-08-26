from supabase_db import supabase_client

def upload_and_update():
    banners = [
        {
            "id": 1,
            "title": "Elevate Your Living Experience",
            "subtitle": "Discover our new premium collection of luxury living room furniture.",
            "file": r"C:\Users\gurup\.gemini\antigravity\brain\2db70d8f-b8ce-4fdf-adbb-3692af666b1c\banner_living_room_1786853133625.jpg"
        },
        {
            "id": 2,
            "title": "Luxury Bedroom Collection",
            "subtitle": "Transform your bedroom into a sanctuary of comfort and style.",
            "file": r"C:\Users\gurup\.gemini\antigravity\brain\2db70d8f-b8ce-4fdf-adbb-3692af666b1c\banner_bedroom_1786853188019.jpg"
        },
        {
            "id": 3,
            "title": "Work From Home In Style",
            "subtitle": "Ergonomic, modern, and beautiful office furniture for maximum productivity.",
            "file": r"C:\Users\gurup\.gemini\antigravity\brain\2db70d8f-b8ce-4fdf-adbb-3692af666b1c\banner_office_1786853203712.jpg"
        }
    ]

    for b in banners:
        filename = f"ai_hero_banner_{b['id']}.jpg"
        with open(b["file"], "rb") as f:
            data = f.read()
        
        try:
            supabase_client.storage.from_('products').upload(filename, data, {'content-type': 'image/jpeg'})
        except Exception as e:
            if "Duplicate" in str(e) or "already exists" in str(e):
                supabase_client.storage.from_('products').update(filename, data, {'content-type': 'image/jpeg'})
            else:
                print(f"Error: {e}")
                
        url = supabase_client.storage.from_('products').get_public_url(filename)
        
        res = supabase_client.table('hero_banners').update({
            'image_url': url,
            'title': b['title'],
            'subtitle': b['subtitle']
        }).eq('id', str(b['id'])).execute()
        
        if not res.data:
            res = supabase_client.table('hero_banners').update({
                'image_url': url,
                'title': b['title'],
                'subtitle': b['subtitle']
            }).eq('id', b['id']).execute()
            
        print(f"Updated banner {b['id']} with url {url}")

if __name__ == '__main__':
    upload_and_update()
