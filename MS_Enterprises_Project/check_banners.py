from supabase_db import supabase_client
res = supabase_client.table('hero_banners').select('*').execute()
for b in res.data:
    print(f"{b['id']}: {b['title']} - {b['image_url']}")
