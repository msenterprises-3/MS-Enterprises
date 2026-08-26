import os
import sqlite3

def run_verification():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'catalogue.db')
    print("MS Enterprises Product Catalogue Verification Utility")
    print("=====================================================")
    
    if not os.path.exists(db_path):
        print(f"[-] Database file not found at: {db_path}")
        print("[!] Please run seed_db.py to generate and populate the database.")
        return False
        
    print(f"[+] Database file found at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables list
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"[+] Discovered tables in database: {', '.join(tables)}")
        
        required_tables = [
            'settings', 'categories', 'subcategories', 'products', 
            'product_images', 'product_variants', 'hero_banners', 
            'offer_banners', 'trust_badges', 'testimonials', 
            'video_testimonials', 'reviews'
        ]
        
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            print(f"[-] Missing database tables: {', '.join(missing_tables)}")
            conn.close()
            return False
            
        print("[+] All 12 required tables exist.")
        
        # Check settings
        cursor.execute("SELECT COUNT(*) FROM settings;")
        settings_count = cursor.fetchone()[0]
        if settings_count == 0:
            print("[-] settings table is empty!")
            conn.close()
            return False
        print("[+] settings table is populated.")
        
        # Check products count
        cursor.execute("SELECT COUNT(*) FROM products;")
        products_count = cursor.fetchone()[0]
        print(f"[+] Total products in database: {products_count}")
        
        # Check categories count
        cursor.execute("SELECT COUNT(*) FROM categories;")
        cat_count = cursor.fetchone()[0]
        print(f"[+] Total categories in database: {cat_count}")
        
        # Check if FTS is set up
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products_fts';")
        fts_exists = cursor.fetchone()
        if fts_exists:
            print("[+] Full Text Search FTS5 virtual table is set up.")
        else:
            print("[-] Full Text Search FTS5 virtual table is NOT present.")
            
        conn.close()
        print("\n[+] Verification PASSED! Database is ready for production.")
        return True
        
    except Exception as e:
        print(f"[-] Database connection error: {e}")
        return False

if __name__ == "__main__":
    run_verification()
