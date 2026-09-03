import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Import the existing SQLite mock as the fallback db client
from sqlite_firestore import db as sqlite_db, clean_id, map_document_data, Increment

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase_client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[Supabase Client] Successfully initialized Supabase client.")
    except Exception as e:
        print(f"[Supabase Client] Initialization error: {e}")

# Authoritative Supabase PostgreSQL column definitions (matching supabase_schema.sql and migrations)
SUPABASE_TABLE_COLUMNS = {
    'settings': {
        'id', 'whatsapp_number', 'contact_email', 'contact_phone', 'contact_address',
        'working_hours', 'google_map_link', 'instagram_url', 'facebook_url',
        'youtube_url', 'admin_password_hash', 'about_story', 'about_mission',
        'about_vision', 'seo_meta_title', 'seo_meta_description', 'wishlist_enabled',
        'cart_enabled', 'cart_min_value', 'whatsapp_cart_prefix', 'whatsapp_wishlist_prefix',
        'updated_at', 'show_facebook', 'show_instagram', 'show_youtube',
        'countdown_enabled', 'countdown_end_date', 'upi_id',
        'standard_delivery_days', 'preorder_delivery_days'
    },
    'categories': {
        'id', 'name', 'slug', 'image_url', 'description', 'display_order', 'status'
    },
    'subcategories': {
        'id', 'category_id', 'name', 'slug', 'display_order', 'status'
    },
    'products': {
        'id', 'category_id', 'subcategory_id', 'name', 'slug', 'sku',
        'short_description', 'description', 'price', 'offer_price', 'offer_badge',
        'status', 'is_featured', 'is_new_arrival', 'is_best_seller', 'is_premium',
        'specifications', 'features', 'display_order', 'wishlist_count', 'cart_count',
        'created_at', 'updated_at', 'dealer_status', 'stock_status', 'stock_quantity', 'allow_preorder'
    },
    'stock_notifications': {
        'id', 'product_id', 'contact_info', 'status', 'created_at'
    },
    'product_images': {
        'id', 'product_id', 'image_url', 'display_order'
    },
    'product_variants': {
        'id', 'product_id', 'name', 'value', 'price_adjustment'
    },
    'hero_banners': {
        'id', 'image_url', 'title', 'subtitle', 'link_text', 'link_url',
        'display_order', 'status'
    },
    'offer_banners': {
        'id', 'image_url', 'title', 'subtitle', 'ending_date', 'button_text',
        'button_link', 'status', 'display_order'
    },
    'trust_badges': {
        'id', 'icon_svg', 'title', 'description', 'display_order'
    },
    'testimonials': {
        'id', 'customer_name', 'customer_photo', 'city', 'rating', 'review',
        'status', 'display_order'
    },
    'video_testimonials': {
        'id', 'customer_name', 'video_url', 'thumbnail_url', 'review_text',
        'status', 'display_order'
    },
    'category_hero_banners': {
        'id', 'category_id', 'image_url', 'title', 'button_text', 'offer_text', 'status'
    },
    'category_offer_banners': {
        'id', 'category_id', 'image_url', 'title', 'product_image_url',
        'product_price', 'discount', 'status'
    },
    'catalogue_updates': {
        'id', 'last_updated'
    },
    'dealers': {
        'id', 'email', 'password_hash', 'business_name', 'dealer_name',
        'mobile_number', 'status', 'created_at', 'gst_number', 'business_address',
        'city', 'state', 'pincode', 'tier'
    },
    'orders': {
        'id', 'session_id', 'mobile_number', 'total_value', 'status',
        'payment_method', 'items_json', 'customer_name', 'shipping_address',
        'created_at', 'email', 'pincode', 'order_notes', 'payment_status', 'order_status'
    },
    'dealer_orders': {
        'id', 'dealer_id', 'business_name', 'total_value', 'status',
        'items_json', 'created_at'
    },
    'cart_items': {
        'id', 'session_id', 'product_id', 'quantity', 'variant_id', 'created_at'
    },
    'wishlist_items': {
        'id', 'session_id', 'product_id', 'created_at'
    },
    'recently_viewed_items': {
        'id', 'session_id', 'product_id', 'viewed_at'
    },
    'reviews': {
        'id', 'product_id', 'reviewer_name', 'rating', 'review_text',
        'status', 'display_order', 'created_at', 'updated_at'
    },
    'dealer_activities': {
        'id', 'dealer_id', 'dealer_name', 'business_name', 'action',
        'details', 'device', 'ip_address', 'created_at', 'mobile_number'
    },
    'bulk_enquiries': {
        'id', 'name', 'email', 'phone', 'message', 'created_at', 'company', 'details'
    },
    'customers': {
        'mobile_number', 'name', 'email', 'address', 'pincode', 'last_active', 'updated_at'
    }
}

def get_valid_columns(collection_name):
    """Returns authoritative valid columns for a Supabase table, or None if unconstrained."""
    return SUPABASE_TABLE_COLUMNS.get(collection_name, None)

class SupabaseDBAdapter:
    def __init__(self):
        self.fallback = sqlite_db
        
    def collection(self, name):
        if supabase_client is None:
            print(f"[Supabase Fallback] Client not initialized. Routing collection '{name}' to SQLite fallback.")
            return self.fallback.collection(name)
        return SupabaseCollectionRef(name, self.fallback)
        
    def batch(self):
        return SupabaseWriteBatch(self.fallback.batch())

# Alias for backwards compatibility
SupabaseFirestoreMock = SupabaseDBAdapter

class SupabaseCollectionRef:
    def __init__(self, name, fallback):
        self.name = name
        self.fallback = fallback
        
    def document(self, doc_id=None):
        if doc_id is None:
            doc_id = uuid.uuid4().hex
        return SupabaseDocumentRef(self.name, doc_id, self.fallback)
        
    def add(self, data):
        doc_id = uuid.uuid4().hex
        doc_ref = SupabaseDocumentRef(self.name, doc_id, self.fallback)
        doc_ref.set(data)
        return None, doc_ref
        
    def where(self, field, op, value):
        return SupabaseQuery(self.name, self.fallback).where(field, op, value)
        
    def order_by(self, field, direction="ASCENDING"):
        return SupabaseQuery(self.name, self.fallback).order_by(field, direction)
        
    def limit(self, count):
        return SupabaseQuery(self.name, self.fallback).limit(count)
        
    def get(self):
        return SupabaseQuery(self.name, self.fallback).get()
        
    def stream(self):
        return SupabaseQuery(self.name, self.fallback).stream()
        
    def on_snapshot(self, callback):
        return None

class SupabaseDocumentRef:
    def __init__(self, collection_name, doc_id, fallback):
        self.collection_name = collection_name
        self.raw_id = doc_id
        self.fallback = fallback
        
        # settings document 'global' maps to row ID 1 in Postgres settings table
        if self.collection_name == 'settings' and str(doc_id) in ('global', '1'):
            self.id = 1
        elif self.collection_name == 'catalogue_updates' and str(doc_id) == '1':
            self.id = 1
        else:
            self.id = clean_id(doc_id)
            
    def _get_pk_col(self):
        if self.collection_name == 'customers':
            return 'mobile_number'
        return 'id'
        
    def get(self):
        pk_col = self._get_pk_col()
        try:
            res = supabase_client.table(self.collection_name).select('*').eq(pk_col, self.id).execute()
            row = res.data[0] if res.data else None
            
            # Auto-inject product images
            if row and self.collection_name == 'products':
                try:
                    img_res = supabase_client.table('product_images').select('image_url').eq('product_id', self.id).execute()
                    row['images'] = [img['image_url'] for img in img_res.data]
                except Exception as img_e:
                    print(f"Error fetching images for product {self.id}: {img_e}")
                    row['images'] = []
                    
            if self.collection_name == 'settings':
                try:
                    fallback_doc = self.fallback.collection('settings').document(self.raw_id).get()
                    if fallback_doc.exists:
                        fb_dict = fallback_doc.to_dict()
                        if row is None:
                            row = fb_dict
                        else:
                            for k, v in fb_dict.items():
                                if k not in row or row[k] is None:
                                    row[k] = v
                except Exception as fb_err:
                    print(f"Settings fallback merge error: {fb_err}")
                    
            return SupabaseDocumentSnapshot(self.collection_name, self.raw_id, row)
        except Exception as e:
            print(f"[Supabase Fallback] Error in document get({self.collection_name}/{self.raw_id}): {e}. Using SQLite fallback.")
            return self.fallback.collection(self.collection_name).document(self.raw_id).get()
            
    def set(self, data, merge=False):
        pk_col = self._get_pk_col()
        insert_data = map_document_data(self.collection_name, data)
        insert_data[pk_col] = self.id
        
        # Sync settings to SQLite fallback if needed
        if self.collection_name == 'settings':
            try:
                self.fallback.collection(self.collection_name).document(self.raw_id).set(data, merge)
            except Exception as fb_e:
                print(f"Error syncing settings set to fallback: {fb_e}")

        valid_cols = get_valid_columns(self.collection_name)
        # Serialize nested lists/dicts to match JSONB columns in Supabase
        for k, v in list(insert_data.items()):
            if valid_cols is not None and k not in valid_cols:
                insert_data.pop(k)
            elif isinstance(v, Increment):
                insert_data[k] = v.value
            elif isinstance(v, (dict, list)):
                pass # keep as dict/list for jsonb columns in Supabase
            elif hasattr(v, 'isoformat'):
                insert_data[k] = v.isoformat()
            elif isinstance(v, datetime):
                insert_data[k] = v.strftime('%Y-%m-%d %H:%M:%S')
                
        try:
            supabase_client.table(self.collection_name).upsert(insert_data).execute()
        except Exception as e:
            print(f"[Supabase Error] Error in document set({self.collection_name}/{self.raw_id}): {e}")
            raise e
            
    def update(self, data):
        pk_col = self._get_pk_col()
        update_data = map_document_data(self.collection_name, data)
        
        # Sync settings to SQLite fallback if needed
        if self.collection_name == 'settings':
            try:
                self.fallback.collection(self.collection_name).document(self.raw_id).update(data)
            except Exception as fb_e:
                print(f"Error syncing settings update to fallback: {fb_e}")

        valid_cols = get_valid_columns(self.collection_name)
        
        has_increment = False
        for k, v in list(update_data.items()):
            if valid_cols is not None and k not in valid_cols:
                update_data.pop(k)
            elif isinstance(v, Increment):
                has_increment = True
                
        if has_increment:
            try:
                res = supabase_client.table(self.collection_name).select('*').eq(pk_col, self.id).execute()
                current_row = res.data[0] if res.data else {}
            except Exception:
                current_row = {}
            for k, v in list(update_data.items()):
                if isinstance(v, Increment):
                    curr_val = current_row.get(k) or 0
                    update_data[k] = curr_val + v.value
                    
        for k, v in list(update_data.items()):
            if isinstance(v, (dict, list)):
                pass
            elif hasattr(v, 'isoformat'):
                update_data[k] = v.isoformat()
            elif isinstance(v, datetime):
                update_data[k] = v.strftime('%Y-%m-%d %H:%M:%S')
                
        if not update_data:
            return
            
        try:
            supabase_client.table(self.collection_name).update(update_data).eq(pk_col, self.id).execute()
        except Exception as e:
            print(f"[Supabase Error] Error in document update({self.collection_name}/{self.raw_id}): {e}")
            raise e
            
    def delete(self):
        pk_col = self._get_pk_col()
        try:
            supabase_client.table(self.collection_name).delete().eq(pk_col, self.id).execute()
        except Exception as e:
            print(f"[Supabase Error] Error in document delete({self.collection_name}/{self.raw_id}): {e}")
            raise e

class SupabaseQuery:
    def __init__(self, collection_name, fallback):
        self.collection_name = collection_name
        self.fallback = fallback
        self.filters = []
        self.orders = []
        self.limit_count = None
        
    def where(self, field, op, value):
        self.filters.append((field, op, value))
        return self
        
    def order_by(self, field, direction="ASCENDING"):
        desc = "DESC" in str(direction).upper()
        self.orders.append((field, desc))
        return self
        
    def limit(self, count):
        self.limit_count = count
        return self
        
    def get(self):
        try:
            q = supabase_client.table(self.collection_name).select('*')
            
            # Apply filters
            for field, op, value in self.filters:
                if op in ('==', '='):
                    q = q.eq(field, value)
                elif op == '>=':
                    q = q.gte(field, value)
                elif op == '<=':
                    q = q.lte(field, value)
                elif op == '>':
                    q = q.gt(field, value)
                elif op == '<':
                    q = q.lt(field, value)
                    
            # Apply ordering
            for field, desc in self.orders:
                q = q.order(field, desc=desc)
                
            # Apply limit
            if self.limit_count is not None:
                q = q.limit(self.limit_count)
                
            res = q.execute()
            rows = res.data or []
            
            if self.collection_name == 'products' and rows:
                try:
                    p_ids = [str(r.get('id')) for r in rows if r.get('id')]
                    if p_ids:
                        img_res = supabase_client.table('product_images').select('product_id, image_url').in_('product_id', p_ids).execute()
                        img_map = {}
                        for img in (img_res.data or []):
                            pid = str(img['product_id'])
                            if pid not in img_map:
                                img_map[pid] = []
                            img_map[pid].append(img['image_url'])
                        for r in rows:
                            r['images'] = img_map.get(str(r.get('id')), [])
                except Exception as e:
                    print(f"Error fetching product images batch: {e}")
                    for r in rows:
                        r['images'] = []
                        
            return [SupabaseDocumentSnapshot(self.collection_name, row.get('id', row.get('mobile_number', '')), row) for row in rows]
        except Exception as e:
            print(f"[Supabase Fallback] Error in query on '{self.collection_name}': {e}. Using SQLite fallback.")
            sq = self.fallback.collection(self.collection_name)
            for field, op, value in self.filters:
                sq = sq.where(field, op, value)
            for field, desc in self.orders:
                dir_ = "DESCENDING" if desc else "ASCENDING"
                sq = sq.order_by(field, dir_)
            if self.limit_count is not None:
                sq = sq.limit(self.limit_count)
            return sq.get()
            
    def stream(self):
        return self.get()

class SupabaseDocumentSnapshot:
    def __init__(self, collection_name, doc_id, row):
        self.collection_name = collection_name
        self._id = doc_id
        self._row = row
        self.exists = row is not None
        
    @property
    def reference(self):
        return db.collection(self.collection_name).document(self._id)
        
    @property
    def id(self):
        if self.collection_name == 'settings' and (self._id == 1 or self._id == '1'):
            return 'global'
        return str(self._id) if self._id is not None else ''
        
    def to_dict(self):
        if not self.exists:
            return {}
        return dict(self._row)

class SupabaseWriteBatch:
    def __init__(self, fallback_batch):
        self.ops = []
        self.fallback_batch = fallback_batch
        
    def set(self, doc_ref, data, merge=False):
        self.ops.append(('set', doc_ref, data))
        fallback_ref = doc_ref.fallback.collection(doc_ref.collection_name).document(doc_ref.raw_id)
        self.fallback_batch.set(fallback_ref, data, merge)
        
    def update(self, doc_ref, data):
        self.ops.append(('update', doc_ref, data))
        fallback_ref = doc_ref.fallback.collection(doc_ref.collection_name).document(doc_ref.raw_id)
        self.fallback_batch.update(fallback_ref, data)
        
    def delete(self, doc_ref):
        self.ops.append(('delete', doc_ref, None))
        fallback_ref = doc_ref.fallback.collection(doc_ref.collection_name).document(doc_ref.raw_id)
        self.fallback_batch.delete(fallback_ref)
        
    def commit(self):
        # 1. Commit to Supabase
        for op, doc_ref, data in self.ops:
            pk_col = doc_ref._get_pk_col()
            valid_cols = get_valid_columns(doc_ref.collection_name)
            if op == 'set':
                insert_data = map_document_data(doc_ref.collection_name, data)
                insert_data[pk_col] = doc_ref.id
                for k, v in list(insert_data.items()):
                    if valid_cols is not None and k not in valid_cols:
                        insert_data.pop(k)
                    elif isinstance(v, Increment):
                        insert_data[k] = v.value
                    elif isinstance(v, (dict, list)):
                        pass
                    elif hasattr(v, 'isoformat'):
                        insert_data[k] = v.isoformat()
                    elif isinstance(v, datetime):
                        insert_data[k] = v.strftime('%Y-%m-%d %H:%M:%S')
                try:
                    supabase_client.table(doc_ref.collection_name).upsert(insert_data).execute()
                except Exception as e:
                    print(f"[Supabase Batch Error] Error setting {doc_ref.collection_name}/{doc_ref.id}: {e}")
                    raise e
            elif op == 'update':
                update_data = map_document_data(doc_ref.collection_name, data)
                has_increment = False
                for k, v in list(update_data.items()):
                    if valid_cols is not None and k not in valid_cols:
                        update_data.pop(k)
                    elif isinstance(v, Increment):
                        has_increment = True
                        
                if has_increment:
                    try:
                        res = supabase_client.table(doc_ref.collection_name).select('*').eq(pk_col, doc_ref.id).execute()
                        current_row = res.data[0] if res.data else {}
                    except Exception:
                        current_row = {}
                    for k, v in list(update_data.items()):
                        if isinstance(v, Increment):
                            curr_val = current_row.get(k) or 0
                            update_data[k] = curr_val + v.value
                            
                for k, v in list(update_data.items()):
                    if isinstance(v, (dict, list)):
                        pass
                    elif hasattr(v, 'isoformat'):
                        update_data[k] = v.isoformat()
                    elif isinstance(v, datetime):
                        update_data[k] = v.strftime('%Y-%m-%d %H:%M:%S')
                try:
                    supabase_client.table(doc_ref.collection_name).update(update_data).eq(pk_col, doc_ref.id).execute()
                except Exception as e:
                    print(f"[Supabase Batch Error] Error updating {doc_ref.collection_name}/{doc_ref.id}: {e}")
                    raise e
            elif op == 'delete':
                try:
                    supabase_client.table(doc_ref.collection_name).delete().eq(pk_col, doc_ref.id).execute()
                except Exception as e:
                    print(f"[Supabase Batch Error] Error deleting {doc_ref.collection_name}/{doc_ref.id}: {e}")
                    raise e
                    
        # 2. Commit to local SQLite backup in WAL mode
        try:
            self.fallback_batch.commit()
        except Exception as e:
            print(f"[Database Batch] SQLite fallback commit note: {e}")

# Export single global client adapter instance
db = SupabaseDBAdapter()
