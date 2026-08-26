import os
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Import the existing SQLite firestore mock as the fallback db client
from sqlite_firestore import db as sqlite_db, clean_id, map_document_data

try:
    from firebase_admin import firestore
except ImportError:
    firestore = None

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

_columns_cache = {}

def get_valid_columns(collection_name):
    if collection_name not in _columns_cache:
        import sqlite3
        try:
            conn = sqlite3.connect(sqlite_db.db_path)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({collection_name})")
            _columns_cache[collection_name] = [row[1] for row in cursor.fetchall()]
            conn.close()
        except Exception:
            return []
    return _columns_cache.get(collection_name, [])

class SupabaseFirestoreMock:
    def __init__(self):
        self.fallback = sqlite_db
        
    def collection(self, name):
        if supabase_client is None:
            print(f"[Supabase Fallback] Client not initialized. Routing collection '{name}' to SQLite fallback.")
            return self.fallback.collection(name)
        return SupabaseCollectionRef(name, self.fallback)
        
    def batch(self):
        return SupabaseWriteBatch(self.fallback.batch())

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
        # Snapshots listener is no-op for Supabase web requests
        print(f"[Supabase Mock] on_snapshot listener ignored for '{self.name}'.")
        return None

class SupabaseDocumentRef:
    def __init__(self, collection_name, doc_id, fallback):
        self.collection_name = collection_name
        self.raw_id = doc_id
        self.fallback = fallback
        
        # settings document 'global' maps to row ID 1 in Postgres settings table
        if self.collection_name == 'settings' and doc_id == 'global':
            self.id = 1
        else:
            self.id = clean_id(doc_id)
            
    def _get_pk_col(self):
        # Autodetect or define primary keys matching our schema
        if self.collection_name in ('settings', 'categories', 'subcategories', 'products', 'product_images', 
                                    'product_variants', 'trust_badges', 'testimonials', 'video_testimonials', 
                                    'category_hero_banners', 'category_offer_banners', 'catalogue_updates', 'hero_banners', 'offer_banners'):
            return 'id'
        return 'id'  # For orders, dealers, cart, reviews, etc., 'id' is TEXT primary key.
        
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
        
        # Always sync settings to SQLite fallback
        if self.collection_name == 'settings':
            try:
                self.fallback.collection(self.collection_name).document(self.raw_id).set(data, merge)
            except Exception as fb_e:
                print(f"Error syncing settings set to fallback: {fb_e}")

        columns = get_valid_columns(self.collection_name)
        # Serialize nested lists/dicts to match JSONB columns in Supabase
        for k, v in list(insert_data.items()):
            if k not in columns:
                insert_data.pop(k)
            elif firestore and isinstance(v, firestore.Increment):
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
            if self.collection_name in ('products', 'orders', 'cart_items', 'customers', 'product_images', 'product_variants'):
                raise e
            print("Using SQLite fallback.")
            self.fallback.collection(self.collection_name).document(self.raw_id).set(data, merge)
            
    def update(self, data):
        pk_col = self._get_pk_col()
        update_data = map_document_data(self.collection_name, data)
        
        # Always sync settings to SQLite fallback
        if self.collection_name == 'settings':
            try:
                self.fallback.collection(self.collection_name).document(self.raw_id).update(data)
            except Exception as fb_e:
                print(f"Error syncing settings update to fallback: {fb_e}")

        columns = get_valid_columns(self.collection_name)
        
        has_increment = False
        for k, v in list(update_data.items()):
            if k not in columns:
                update_data.pop(k)
            elif firestore and isinstance(v, firestore.Increment):
                has_increment = True
                
        if has_increment:
            try:
                res = supabase_client.table(self.collection_name).select('*').eq(pk_col, self.id).execute()
                current_row = res.data[0] if res.data else {}
            except Exception:
                current_row = {}
            for k, v in list(update_data.items()):
                if firestore and isinstance(v, firestore.Increment):
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
            supabase_client.table(self.collection_name).update(update_data).eq(pk_col, self.id).execute()
        except Exception as e:
            print(f"[Supabase Error] Error in document update({self.collection_name}/{self.raw_id}): {e}")
            if self.collection_name in ('products', 'orders', 'cart_items', 'customers', 'product_images', 'product_variants'):
                raise e
            print("Using SQLite fallback.")
            self.fallback.collection(self.collection_name).document(self.raw_id).update(data)
            
    def delete(self):
        pk_col = self._get_pk_col()
        try:
            supabase_client.table(self.collection_name).delete().eq(pk_col, self.id).execute()
        except Exception as e:
            print(f"[Supabase Error] Error in document delete({self.collection_name}/{self.raw_id}): {e}")
            if self.collection_name in ('products', 'orders', 'cart_items', 'customers', 'product_images', 'product_variants'):
                raise e
            print("Using SQLite fallback.")
            self.fallback.collection(self.collection_name).document(self.raw_id).delete()

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
        desc = "DESC" in direction.upper()
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
            rows = res.data
            
            if self.collection_name == 'products' and rows:
                try:
                    p_ids = [str(r.get('id')) for r in rows if r.get('id')]
                    if p_ids:
                        img_res = supabase_client.table('product_images').select('product_id, image_url').in_('product_id', p_ids).execute()
                        img_map = {}
                        for img in img_res.data:
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
                        
            return [SupabaseDocumentSnapshot(self.collection_name, row.get('id', ''), row) for row in rows]
        except Exception as e:
            print(f"[Supabase Fallback] Error in query on '{self.collection_name}': {e}. Using SQLite fallback.")
            # Build sqlite fallback query
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
        if self.collection_name == 'settings' and self._id == 1:
            return 'global'
        return str(self._id) if self._id is not None else ''
        
    def to_dict(self):
        if not self.exists:
            return {}
        # Return row dict directly (JSONB fields are already parsed by Supabase SDK!)
        return dict(self._row)

class SupabaseWriteBatch:
    def __init__(self, fallback_batch):
        self.ops = []
        self.fallback_batch = fallback_batch
        
    def set(self, doc_ref, data, merge=False):
        self.ops.append(('set', doc_ref, data))
        # Sync to SQLite fallback batch
        fallback_ref = doc_ref.fallback.collection(doc_ref.collection_name).document(doc_ref.raw_id)
        self.fallback_batch.set(fallback_ref, data, merge)
        
    def update(self, doc_ref, data):
        self.ops.append(('update', doc_ref, data))
        # Sync to SQLite fallback batch
        fallback_ref = doc_ref.fallback.collection(doc_ref.collection_name).document(doc_ref.raw_id)
        self.fallback_batch.update(fallback_ref, data)
        
    def delete(self, doc_ref):
        self.ops.append(('delete', doc_ref, None))
        # Sync to SQLite fallback batch
        fallback_ref = doc_ref.fallback.collection(doc_ref.collection_name).document(doc_ref.raw_id)
        self.fallback_batch.delete(fallback_ref)
        
    def commit(self):
        # 1. Commit to Supabase
        for op, doc_ref, data in self.ops:
            pk_col = doc_ref._get_pk_col()
            columns = get_valid_columns(doc_ref.collection_name)
            if op == 'set':
                insert_data = map_document_data(doc_ref.collection_name, data)
                insert_data[pk_col] = doc_ref.id
                for k, v in list(insert_data.items()):
                    if k not in columns:
                        insert_data.pop(k)
                    elif firestore and isinstance(v, firestore.Increment):
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
                    print(f"[Supabase Batch] Error setting {doc_ref.collection_name}/{doc_ref.id}: {e}")
            elif op == 'update':
                update_data = map_document_data(doc_ref.collection_name, data)
                has_increment = False
                for k, v in list(update_data.items()):
                    if k not in columns:
                        update_data.pop(k)
                    elif firestore and isinstance(v, firestore.Increment):
                        has_increment = True
                        
                if has_increment:
                    try:
                        res = supabase_client.table(doc_ref.collection_name).select('*').eq(pk_col, doc_ref.id).execute()
                        current_row = res.data[0] if res.data else {}
                    except Exception:
                        current_row = {}
                    for k, v in list(update_data.items()):
                        if firestore and isinstance(v, firestore.Increment):
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
                    print(f"[Supabase Batch] Error updating {doc_ref.collection_name}/{doc_ref.id}: {e}")
            elif op == 'delete':
                try:
                    supabase_client.table(doc_ref.collection_name).delete().eq(pk_col, doc_ref.id).execute()
                except Exception as e:
                    print(f"[Supabase Batch] Error deleting {doc_ref.collection_name}/{doc_ref.id}: {e}")
                    
        # 2. Commit to local SQLite backup in WAL mode
        try:
            self.fallback_batch.commit()
            print("[Database Batch] Committed batch transactions to SQLite fallback.")
        except Exception as e:
            print(f"[Database Batch] SQLite fallback commit error: {e}")

# Export single global client adapter instance
db = SupabaseFirestoreMock()

