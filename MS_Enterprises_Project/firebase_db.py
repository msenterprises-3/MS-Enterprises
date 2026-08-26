import os
import threading
from datetime import datetime
import certifi

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def configure_grpc_ssl():
    import ssl
    pem_certs = ""
    try:
        with open(certifi.where(), "r", encoding="utf-8") as f:
            pem_certs = f.read()
    except Exception as e:
        print(f"Warning reading certifi CA bundle: {e}")
        
    try:
        if hasattr(ssl, 'enum_certificates'):
            win_count = 0
            for store_name in ["ROOT", "CA", "MY"]:
                for cert, encoding, trust in ssl.enum_certificates(store_name):
                    if encoding == "x509_asn":
                        try:
                            pem_certs += "\n" + ssl.DER_cert_to_PEM_cert(cert)
                            win_count += 1
                        except Exception:
                            pass
            if win_count > 0:
                print(f"Appended {win_count} Windows certificate store roots.")
    except Exception as e:
        print(f"Notice on certificate enumeration: {e}")
        
    project_dir = os.path.dirname(os.path.abspath(__file__))
    cert_path = os.path.join(project_dir, "wincerts.pem").replace("\\", "/")
    try:
        with open(cert_path, "w", encoding="utf-8") as f:
            f.write(pem_certs)
        os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = cert_path
    except Exception:
        os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = certifi.where()

configure_grpc_ssl()

import json

# Lock for thread-safety in Flask
_cache_lock = threading.Lock()

# Global cache variables
_cache = {}
_last_update_check = None

from supabase_db import db

def clean_id(doc_id):
    try:
        if str(doc_id).isdigit():
            return int(doc_id)
    except Exception:
        pass
    return doc_id

DEFAULT_SETTINGS = {
    'about_mission': 'Our mission is to provide premium quality furniture.',
    'about_story': 'MS Enterprises was founded with a vision to deliver premium quality furniture and exceptional design services.',
    'about_vision': 'To become a household name in premium luxury furniture.',
    'cart_enabled': True,
    'cart_min_value': 0.0,
    'contact_address': 'MS Enterprises, Main Road, Beside TSR Function Hall, Mannuru, Rajampet, Andhra Pradesh – 516126',
    'contact_email': 'sales@msenterprises.com',
    'contact_phone': '+91 96766 67998',
    'countdown_enabled': False,
    'countdown_end_date': '',
    'facebook_url': 'https://facebook.com/msenterprises',
    'google_map_link': '',
    'instagram_url': 'https://www.instagram.com/msenterprises.rjp?igsi=MXV5bHB6Yzdicjk1dA==',
    'seo_meta_description': 'MS Enterprises - Your Style, Your Space, Your Furniture.',
    'seo_meta_title': 'MS Enterprises | Luxury Home & Living Furniture Catalogue',
    'show_facebook': True,
    'show_instagram': True,
    'show_youtube': True,
    'upi_id': '9676667998@ybl',
    'whatsapp_cart_prefix': 'Hello MS Enterprises, I would like to order:',
    'whatsapp_number': '919676667998',
    'whatsapp_wishlist_prefix': 'Hello MS Enterprises, here is my wishlist:',
    'wishlist_enabled': True,
    'working_hours': '10:00 AM - 08:30 PM (Mon-Sun)',
    'youtube_url': 'https://youtube.com/@msfurnituregallery?si=J8Hr65D-y4w7G2Uc'
}

def load_from_sqlite():
    """Loads all data from local SQLite database (instance/catalogue.db) into memory cache."""
    import sqlite3
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'catalogue.db')
    if not os.path.exists(db_path):
        print(f"[SQLite Fallback] Database file not found at {db_path}!")
        return {}
        
    print("[SQLite Fallback] Loading catalogue data from local SQLite database...")
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Settings
        settings = {}
        cursor.execute("SELECT * FROM settings LIMIT 1")
        settings_row = cursor.fetchone()
        if settings_row:
            settings = dict(settings_row)
            settings.pop('id', None)
            for bool_key in ['wishlist_enabled', 'cart_enabled', 'show_facebook', 'show_instagram', 'show_youtube', 'countdown_enabled']:
                if bool_key in settings and settings[bool_key] is not None:
                    settings[bool_key] = bool(settings[bool_key])
            
        # 2. Categories
        categories = []
        cursor.execute("SELECT * FROM categories")
        for row in cursor.fetchall():
            d = dict(row)
            d['id'] = clean_id(d['id'])
            categories.append(d)
        categories.sort(key=lambda x: x.get('display_order', 0))
            
        # 3. Subcategories
        subcategories = []
        cursor.execute("SELECT * FROM subcategories")
        for row in cursor.fetchall():
            d = dict(row)
            d['id'] = clean_id(d['id'])
            subcategories.append(d)
        subcategories.sort(key=lambda x: x.get('display_order', 0))
            
        # 4. Products
        products = []
        cursor.execute("SELECT * FROM products")
        for row in cursor.fetchall():
            d = dict(row)
            d['id'] = clean_id(d['id'])
            d['wishlist_count'] = d.get('wishlist_count', 0)
            d['cart_count'] = d.get('cart_count', 0)
            
            try:
                d['specifications'] = json.loads(d['specifications']) if d.get('specifications') else {}
            except Exception:
                d['specifications'] = {}
            try:
                d['features'] = json.loads(d['features']) if d.get('features') else []
            except Exception:
                d['features'] = []
                
            specs = d.get('specifications', {})
            if isinstance(specs, str):
                try:
                    specs = json.loads(specs)
                    d['specifications'] = specs
                except:
                    pass
            
            w_price = 0.0
            if isinstance(specs, dict) and '_wholesale_price' in specs:
                try:
                    w_price = float(specs.pop('_wholesale_price'))
                except:
                    pass

            d['dealer_prices'] = {'default': w_price}
            d['wholesale_price'] = w_price

            d['dealer_status'] = d.get('dealer_status', 'visible')

            if 'created_at' in d and hasattr(d['created_at'], 'isoformat'):
                d['created_at'] = d['created_at'].isoformat()
                
            p_cursor = conn.cursor()
            p_cursor.execute("SELECT image_url FROM product_images WHERE product_id = ? ORDER BY display_order", (d['id'],))
            d['images'] = [r[0] for r in p_cursor.fetchall()]
            if not d['images']:
                d['images'] = ['/static/uploads/products/prod_generic_1.webp']
                
            products.append(d)
            
        products.sort(key=lambda x: (x.get('display_order', 0), x.get('created_at', '')), reverse=True)
            
        # 5. Hero Banners
        hero_banners = []
        cursor.execute("SELECT * FROM hero_banners")
        for row in cursor.fetchall():
            d = dict(row)
            d['id'] = clean_id(d['id'])
            hero_banners.append(d)
        hero_banners.sort(key=lambda x: x.get('display_order', 0))
            
        # 6. Offer Banners
        offer_banners = []
        cursor.execute("SELECT * FROM offer_banners")
        for row in cursor.fetchall():
            d = dict(row)
            d['id'] = clean_id(d['id'])
            offer_banners.append(d)
        offer_banners.sort(key=lambda x: x.get('display_order', 0))
            
        # 7. Trust Badges
        trust_badges = []
        cursor.execute("SELECT * FROM trust_badges")
        for row in cursor.fetchall():
            d = dict(row)
            d['id'] = clean_id(d['id'])
            trust_badges.append(d)
        trust_badges.sort(key=lambda x: x.get('display_order', 0))
            
        # 8. Testimonials
        testimonials = []
        cursor.execute("SELECT * FROM testimonials")
        for row in cursor.fetchall():
            d = dict(row)
            d['id'] = clean_id(d['id'])
            testimonials.append(d)
        testimonials.sort(key=lambda x: x.get('display_order', 0))
            
        # 9. Video Testimonials
        video_testimonials = []
        cursor.execute("SELECT * FROM video_testimonials")
        for row in cursor.fetchall():
            d = dict(row)
            d['id'] = clean_id(d['id'])
            video_testimonials.append(d)
        video_testimonials.sort(key=lambda x: x.get('display_order', 0))

        # 10. Category Hero Banners
        category_hero_banners = []
        cursor.execute("SELECT * FROM category_hero_banners")
        for row in cursor.fetchall():
            d = dict(row)
            d['id'] = clean_id(d['id'])
            category_hero_banners.append(d)

        # 11. Category Offer Banners
        category_offer_banners = []
        cursor.execute("SELECT * FROM category_offer_banners")
        for row in cursor.fetchall():
            d = dict(row)
            d['id'] = clean_id(d['id'])
            category_offer_banners.append(d)

        # 12. Reviews
        reviews = []
        try:
            cursor.execute("SELECT * FROM reviews")
            for row in cursor.fetchall():
                d = dict(row)
                d['id'] = clean_id(d['id'])
                reviews.append(d)
        except Exception:
            pass
            
        conn.close()
        print(f"[SQLite Fallback] Successfully loaded {len(products)} products, {len(categories)} categories from SQLite.")
        return {
            'settings': settings,
            'categories': categories,
            'subcategories': subcategories,
            'products': products,
            'hero_banners': hero_banners,
            'offer_banners': offer_banners,
            'trust_badges': trust_badges,
            'testimonials': testimonials,
            'video_testimonials': video_testimonials,
            'category_hero_banners': category_hero_banners,
            'category_offer_banners': category_offer_banners,
            'reviews': reviews
        }
    except Exception as e:
        print(f"[SQLite Fallback] Error reading SQLite database: {e}")
        return {}

def force_reload_cache():
    """Reads all collections from primary database (Supabase PostgreSQL via adapter) into memory cache,
    and falls back to SQLite only if Supabase data is unavailable or empty."""
    global _cache
    with _cache_lock:
        print("[Database Cache] Loading catalogue from primary Supabase PostgreSQL database...")
        
        # 1. Settings (Global configuration)
        settings = {}
        try:
            settings_ref = db.collection('settings').document('global').get()
            settings = settings_ref.to_dict() if settings_ref.exists else {}
            for bool_key in ['wishlist_enabled', 'cart_enabled', 'show_facebook', 'show_instagram', 'show_youtube', 'countdown_enabled']:
                if bool_key in settings and settings[bool_key] is not None:
                    settings[bool_key] = bool(settings[bool_key])
        except Exception as e:
            print(f"[Firebase Cache] Settings load error: {e}")
            
        # 2. Categories
        categories = []
        try:
            for doc in db.collection('categories').stream():
                d = doc.to_dict()
                d['id'] = clean_id(doc.id)
                categories.append(d)
            categories.sort(key=lambda x: x.get('display_order', 0))
        except Exception as e:
            print(f"[Firebase Cache] Categories load error: {e}")
            
        # 3. Subcategories
        subcategories = []
        try:
            for doc in db.collection('subcategories').stream():
                d = doc.to_dict()
                d['id'] = clean_id(doc.id)
                subcategories.append(d)
            subcategories.sort(key=lambda x: x.get('display_order', 0))
        except Exception as e:
            print(f"[Firebase Cache] Subcategories load error: {e}")
            
        # 4. Products
        products = []
        try:
            for doc in db.collection('products').stream():
                d = doc.to_dict()
                d['id'] = clean_id(doc.id)
                d['wishlist_count'] = d.get('wishlist_count', 0)
                d['cart_count'] = d.get('cart_count', 0)
                
                specs = d.get('specifications', {})
                if isinstance(specs, str):
                    try:
                        specs = json.loads(specs)
                        d['specifications'] = specs
                    except:
                        pass
                
                w_price = 0.0
                if isinstance(specs, dict) and '_wholesale_price' in specs:
                    try:
                        w_price = float(specs.pop('_wholesale_price'))
                    except:
                        pass

                d['dealer_prices'] = {'default': w_price}
                d['wholesale_price'] = w_price

                d['dealer_status'] = d.get('dealer_status', 'visible')

                if 'created_at' in d and hasattr(d['created_at'], 'isoformat'):
                    d['created_at'] = d['created_at'].isoformat()
                products.append(d)
            products.sort(key=lambda x: (x.get('display_order', 0), x.get('created_at', '')), reverse=True)
        except Exception as e:
            print(f"[Firebase Cache] Products load error: {e}")
            
        # 5. Hero Banners
        hero_banners = []
        try:
            for doc in db.collection('hero_banners').stream():
                d = doc.to_dict()
                d['id'] = clean_id(doc.id)
                hero_banners.append(d)
            hero_banners.sort(key=lambda x: x.get('display_order', 0))
        except Exception as e:
            print(f"[Firebase Cache] Hero banners load error: {e}")
            
        # 6. Offer Banners
        offer_banners = []
        try:
            for doc in db.collection('offer_banners').stream():
                d = doc.to_dict()
                d['id'] = clean_id(doc.id)
                offer_banners.append(d)
            offer_banners.sort(key=lambda x: x.get('display_order', 0))
        except Exception as e:
            print(f"[Firebase Cache] Offer banners load error: {e}")
            
        # 7. Trust Badges
        trust_badges = []
        try:
            for doc in db.collection('trust_badges').stream():
                d = doc.to_dict()
                d['id'] = clean_id(doc.id)
                trust_badges.append(d)
            trust_badges.sort(key=lambda x: x.get('display_order', 0))
        except Exception as e:
            print(f"[Firebase Cache] Trust badges load error: {e}")
            
        # 8. Testimonials
        testimonials = []
        try:
            for doc in db.collection('testimonials').stream():
                d = doc.to_dict()
                d['id'] = clean_id(doc.id)
                testimonials.append(d)
            testimonials.sort(key=lambda x: x.get('display_order', 0))
        except Exception as e:
            print(f"[Firebase Cache] Testimonials load error: {e}")
            
        # 9. Video Testimonials
        video_testimonials = []
        try:
            for doc in db.collection('video_testimonials').stream():
                d = doc.to_dict()
                d['id'] = clean_id(doc.id)
                video_testimonials.append(d)
            video_testimonials.sort(key=lambda x: x.get('display_order', 0))
        except Exception as e:
            print(f"[Firebase Cache] Video testimonials load error: {e}")

        # 10. Category Hero Banners
        category_hero_banners = []
        try:
            for doc in db.collection('category_hero_banners').stream():
                d = doc.to_dict()
                d['id'] = clean_id(doc.id)
                category_hero_banners.append(d)
        except Exception as e:
            print(f"[Firebase Cache] Category hero banners load error: {e}")

        # 11. Category Offer Banners
        category_offer_banners = []
        try:
            for doc in db.collection('category_offer_banners').stream():
                d = doc.to_dict()
                d['id'] = clean_id(doc.id)
                category_offer_banners.append(d)
        except Exception as e:
            print(f"[Firebase Cache] Category offer banners load error: {e}")
            
        # 12. Reviews
        reviews = []
        try:
            for doc in db.collection('reviews').stream():
                d = doc.to_dict()
                d['id'] = clean_id(doc.id)
                reviews.append(d)
        except Exception as e:
            print(f"[Firebase Cache] Reviews load error: {e}")
            
        # Check if the Firestore load was successful and returned data.
        # If it returned 0 products or 0 categories, or if there was a load error,
        # fall back to local SQLite database!
        if not products or not categories:
            print("[Firebase Cache] Firestore products/categories cache is empty (likely 429 Quota Exceeded). Falling back to local SQLite database...")
            sqlite_cache = load_from_sqlite()
            if sqlite_cache:
                _cache = sqlite_cache
                print("[Firebase Cache] Fallback successful. Loaded from SQLite.")
            else:
                _cache = {
                    'settings': settings,
                    'categories': categories,
                    'subcategories': subcategories,
                    'products': products,
                    'hero_banners': hero_banners,
                    'offer_banners': offer_banners,
                    'trust_badges': trust_badges,
                    'testimonials': testimonials,
                    'video_testimonials': video_testimonials,
                    'category_hero_banners': category_hero_banners,
                    'category_offer_banners': category_offer_banners,
                    'reviews': reviews
                }
        else:
            _cache = {
                'settings': settings,
                'categories': categories,
                'subcategories': subcategories,
                'products': products,
                'hero_banners': hero_banners,
                'offer_banners': offer_banners,
                'trust_badges': trust_badges,
                'testimonials': testimonials,
                'video_testimonials': video_testimonials,
                'category_hero_banners': category_hero_banners,
                'category_offer_banners': category_offer_banners,
                'reviews': reviews
            }
        print(f"[Firebase Cache] Successfully loaded {len(_cache.get('products', []))} products, {len(_cache.get('categories', []))} categories, {len(_cache.get('reviews', []))} reviews, and settings.")

_last_check_time = None

def check_and_sync_cache():
    """Compares the local cache timestamp with the firestore catalogue_updates log.
    Reloads all data if a remote change has occurred."""
    global _last_update_check, _last_check_time
    now = datetime.now()
    if _cache and _last_check_time and (now - _last_check_time).total_seconds() < 5.0:
        return
    _last_check_time = now
    try:
        update_ref = db.collection('catalogue_updates').document('1').get()
        if update_ref.exists:
            remote_time = update_ref.to_dict().get('last_updated')
            if remote_time:
                if not _cache or _last_update_check != remote_time:
                    _last_update_check = remote_time
                    force_reload_cache()
        else:
            if not _cache:
                force_reload_cache()
    except Exception as e:
        print(f"[Firebase Cache] Sync warning: {e}. Falling back to default force load.")
        if not _cache:
            force_reload_cache()

def get_cache(key):
    """Safely retrieves a collection from the memory cache."""
    check_and_sync_cache()
    return _cache.get(key, [])

def get_settings():
    """Safely retrieves global settings dict with defaults for all keys."""
    check_and_sync_cache()
    # Merge loaded settings on top of default settings
    merged = dict(DEFAULT_SETTINGS)
    loaded = _cache.get('settings', {})
    if loaded:
        merged.update(loaded)
    return merged

def get_last_update_time():
    """Returns the cached last update timestamp, updating it if expired."""
    try:
        check_and_sync_cache()
    except Exception:
        pass
    return _last_update_check or ""

def touch_catalogue_update():
    """Modifies the firestore last_updated timestamp to alert all server cache instances and clients."""
    try:
        now = datetime.utcnow().isoformat()
        db.collection('catalogue_updates').document('1').set({
            'last_updated': now
        })
        global _last_update_check
        _last_update_check = now
        force_reload_cache()
    except Exception as e:
        print(f"[Firebase Admin] Error touching updates log: {e}")

# Real-time synchronization support using Firestore on_snapshot
import queue

class MessageAnnouncer:
    def __init__(self):
        self.listeners = []

    def listen(self):
        q = queue.Queue(maxsize=10)
        self.listeners.append(q)
        return q

    def announce(self, msg):
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(msg)
            except queue.Full:
                pass
            except Exception:
                self.listeners.pop(i)

product_announcer = MessageAnnouncer()
_listener_initialized = False

def start_products_listener():
    global _listener_initialized
    if _listener_initialized:
        return
    _listener_initialized = True
    
    def on_products_snapshot(col_snapshot, changes, read_time):
        print(f"[Firebase Listener] Snapshot received with {len(col_snapshot)} products.")
        global _cache
        with _cache_lock:
            products = []
            for doc in col_snapshot:
                d = doc.to_dict()
                d['id'] = clean_id(doc.id)
                d['wishlist_count'] = d.get('wishlist_count', 0)
                d['cart_count'] = d.get('cart_count', 0)
                
                # B2B tier prices
                specs = d.get('specifications', {})
                if isinstance(specs, str):
                    try:
                        specs = json.loads(specs)
                        d['specifications'] = specs
                    except:
                        pass
                
                w_price = 0.0
                if isinstance(specs, dict) and '_wholesale_price' in specs:
                    try:
                        w_price = float(specs.pop('_wholesale_price'))
                    except:
                        pass

                d['dealer_prices'] = {'default': w_price}
                d['wholesale_price'] = w_price

                d['dealer_status'] = d.get('dealer_status', 'visible')

                if 'created_at' in d and hasattr(d['created_at'], 'isoformat'):
                    d['created_at'] = d['created_at'].isoformat()
                if 'updated_at' in d and hasattr(d['updated_at'], 'isoformat'):
                    d['updated_at'] = d['updated_at'].isoformat()
                products.append(d)
                
            # Sort products
            if products or not _cache.get('products'):
                _cache['products'] = products
            
        print("[Firebase Listener] In-memory products cache updated from snapshot.")
        product_announcer.announce("update")

    db.collection('products').on_snapshot(on_products_snapshot)
    print("[Firebase Listener] Firestore products on_snapshot listener active.")

# Start listener on import
start_products_listener()
