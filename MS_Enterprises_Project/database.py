import os
import sqlite3
import json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'catalogue.db')

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        whatsapp_number TEXT DEFAULT '+91 96766 67998',
        contact_email TEXT DEFAULT 'msfurnitureglry@gmail.com',
        contact_phone TEXT DEFAULT '+91 96766 67998',
        contact_address TEXT DEFAULT 'MS Furniture Gallery, Main Road, Beside TSR Function Hall, Mannuru, Rajampet, Andhra Pradesh – 516126',
        working_hours TEXT DEFAULT '10:00 AM - 08:30 PM (Mon-Sun)',
        google_map_link TEXT DEFAULT 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3844.8239088619623!2d79.16010537484433!3d14.19502759006059!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3bb2b2ba119cbf41%3A0xf7de7a0e3f169f4c!2sTSR%20Kalyanamandapam!5e0!3m2!1sen!2sin!4v1700000000000',
        instagram_url TEXT DEFAULT 'https://www.instagram.com/msenterprises.rjp?igsi=MXV5bHB6Yzdicjk1dA==',
        facebook_url TEXT DEFAULT 'https://facebook.com/msenterprises',
        youtube_url TEXT DEFAULT 'https://youtube.com/@msfurnituregallery?si=J8Hr65D-y4w7G2Uc',
        admin_password_hash TEXT NOT NULL,
        about_story TEXT DEFAULT 'MS Furniture Gallery has been the pioneer of luxury home styling since 2012. We bring curated luxury furniture from across the globe directly to your home at unbeatable prices.',
        about_mission TEXT DEFAULT 'To offer high-end, premium quality furniture solutions that elevate Indian homes, making international standards accessible without custom duties or complex import pipelines.',
        about_vision TEXT DEFAULT 'To build India''s most trusted and direct-to-customer furniture and home lifestyle catalog brand, powered by instant WhatsApp communication.',
        seo_meta_title TEXT DEFAULT 'Premium Home & Office Furniture Catalogue | MS Furniture Gallery',
        seo_meta_description TEXT DEFAULT 'Explore MS Furniture Gallery'' exclusive furniture collection. Premium beds, sofas, dining tables, and office setups. Order directly on WhatsApp.'
    );
    """)

    # Categories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        image_url TEXT,
        description TEXT,
        display_order INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active'
    );
    """)

    # Subcategories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subcategories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        display_order INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
    );
    """)

    # Products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        subcategory_id INTEGER,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        sku TEXT,
        short_description TEXT,
        description TEXT,
        price REAL,
        offer_price REAL,
        offer_badge TEXT,
        status TEXT DEFAULT 'active',
        is_featured INTEGER DEFAULT 0,
        is_new_arrival INTEGER DEFAULT 0,
        is_best_seller INTEGER DEFAULT 0,
        is_premium INTEGER DEFAULT 0,
        specifications TEXT, -- JSON string
        features TEXT,       -- JSON string (list of features)
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL,
        FOREIGN KEY (subcategory_id) REFERENCES subcategories (id) ON DELETE SET NULL
    );
    """)

    # Product Images table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        image_url TEXT NOT NULL,
        display_order INTEGER DEFAULT 0,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
    );
    """)

    # Product Variants table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_variants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        name TEXT NOT NULL, -- e.g., 'Size', 'Color', 'Material'
        value TEXT NOT NULL, -- e.g., 'King Size', 'Teak Wood'
        price_adjustment REAL DEFAULT 0.0,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
    );
    """)

    # Hero Banners table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hero_banners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_url TEXT NOT NULL,
        title TEXT,
        subtitle TEXT,
        link_text TEXT,
        link_url TEXT,
        display_order INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active'
    );
    """)

    # Offer Banners table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS offer_banners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_url TEXT NOT NULL,
        title TEXT,
        subtitle TEXT,
        ending_date TEXT, -- Date format 'YYYY-MM-DD HH:MM:SS'
        button_text TEXT,
        button_link TEXT,
        display_order INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active'
    );
    """)

    # Trust Badges table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trust_badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        icon_svg TEXT,
        title TEXT NOT NULL,
        description TEXT,
        display_order INTEGER DEFAULT 0
    );
    """)

    # Testimonials table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS testimonials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        customer_photo TEXT,
        city TEXT,
        rating INTEGER DEFAULT 5,
        review TEXT NOT NULL,
        status TEXT DEFAULT 'active'
    );
    """)

    # Video Testimonials table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS video_testimonials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        video_url TEXT NOT NULL,
        thumbnail_url TEXT,
        review_text TEXT,
        status TEXT DEFAULT 'active'
    );
    """)

    # Category Hero Banners table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS category_hero_banners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        image_url TEXT NOT NULL,
        title TEXT,
        button_text TEXT DEFAULT 'Explore Collection',
        offer_text TEXT,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
    );
    """)

    # Category Offer Banners table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS category_offer_banners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        image_url TEXT NOT NULL,
        title TEXT,
        product_image_url TEXT,
        product_price REAL,
        discount TEXT,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
    );
    """)

    # Reviews table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        reviewer_name TEXT NOT NULL,
        rating INTEGER NOT NULL,
        review_text TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
    );
    """)

    # Cart Items table for guest storage in database
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER DEFAULT 1,
        variant_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
    );
    """)

    # Wishlist Items table for guest storage in database
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wishlist_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        product_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
        UNIQUE(session_id, product_id)
    );
    """)

    # Recently Viewed Items table for guest storage in database
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recently_viewed_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        product_id INTEGER NOT NULL,
        viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
        UNIQUE(session_id, product_id) ON CONFLICT REPLACE
    );
    """)

    # Dealers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dealers (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        business_name TEXT,
        dealer_name TEXT,
        mobile_number TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # B2C Orders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        session_id TEXT,
        mobile_number TEXT,
        total_value REAL,
        status TEXT DEFAULT 'pending',
        payment_method TEXT,
        items_json TEXT,
        customer_name TEXT,
        shipping_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # B2B Dealer Orders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dealer_orders (
        id TEXT PRIMARY KEY,
        dealer_id TEXT,
        business_name TEXT,
        total_value REAL,
        status TEXT DEFAULT 'pending',
        items_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (dealer_id) REFERENCES dealers (id) ON DELETE SET NULL
    );
    """)

    # Dealer Activities table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dealer_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dealer_id TEXT,
        dealer_name TEXT,
        business_name TEXT,
        action TEXT,
        details TEXT,
        device TEXT,
        ip_address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Bulk Enquiries table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bulk_enquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Catalogue Update logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS catalogue_updates (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("INSERT OR IGNORE INTO catalogue_updates(id, last_updated) VALUES(1, CURRENT_TIMESTAMP);")

    # DB Triggers to automatically update catalogue_updates.last_updated on changes
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_products_update_log AFTER UPDATE ON products BEGIN
        UPDATE catalogue_updates SET last_updated = CURRENT_TIMESTAMP WHERE id = 1;
    END;
    """)
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_products_insert_log AFTER INSERT ON products BEGIN
        UPDATE catalogue_updates SET last_updated = CURRENT_TIMESTAMP WHERE id = 1;
    END;
    """)
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_products_delete_log AFTER DELETE ON products BEGIN
        UPDATE catalogue_updates SET last_updated = CURRENT_TIMESTAMP WHERE id = 1;
    END;
    """)
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_settings_update_log AFTER UPDATE ON settings BEGIN
        UPDATE catalogue_updates SET last_updated = CURRENT_TIMESTAMP WHERE id = 1;
    END;
    """)
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_categories_update_log AFTER UPDATE ON categories BEGIN
        UPDATE catalogue_updates SET last_updated = CURRENT_TIMESTAMP WHERE id = 1;
    END;
    """)
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_categories_insert_log AFTER INSERT ON categories BEGIN
        UPDATE catalogue_updates SET last_updated = CURRENT_TIMESTAMP WHERE id = 1;
    END;
    """)
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_categories_delete_log AFTER DELETE ON categories BEGIN
        UPDATE catalogue_updates SET last_updated = CURRENT_TIMESTAMP WHERE id = 1;
    END;
    """)
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_subcategories_update_log AFTER UPDATE ON subcategories BEGIN
        UPDATE catalogue_updates SET last_updated = CURRENT_TIMESTAMP WHERE id = 1;
    END;
    """)
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_subcategories_insert_log AFTER INSERT ON subcategories BEGIN
        UPDATE catalogue_updates SET last_updated = CURRENT_TIMESTAMP WHERE id = 1;
    END;
    """)
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_subcategories_delete_log AFTER DELETE ON subcategories BEGIN
        UPDATE catalogue_updates SET last_updated = CURRENT_TIMESTAMP WHERE id = 1;
    END;
    """)

    # Create Indexes for optimization
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_subcategory ON products(subcategory_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_flags ON products(is_featured, is_new_arrival, is_best_seller, is_premium);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_price ON products(price, offer_price);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_subcategories_category ON subcategories(category_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cart_session ON cart_items(session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wishlist_session ON wishlist_items(session_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recent_session ON recently_viewed_items(session_id);")

    # Try creating FTS5 virtual table for full-text search. SQLite FTS5 is extremely fast.
    try:
        cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(name, short_description, description, content='products', content_rowid='id');")
        
        # Trigger to insert FTS on new product
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_products_ai AFTER INSERT ON products BEGIN
            INSERT INTO products_fts(rowid, name, short_description, description)
            VALUES (new.id, new.name, new.short_description, new.description);
        END;
        """)

        # Trigger to delete FTS on deleted product
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_products_ad AFTER DELETE ON products BEGIN
            INSERT INTO products_fts(products_fts, rowid, name, short_description, description)
            VALUES('delete', old.id, old.name, old.short_description, old.description);
        END;
        """)

        # Trigger to update FTS on product edit
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS trg_products_au AFTER UPDATE ON products BEGIN
            INSERT INTO products_fts(products_fts, rowid, name, short_description, description)
            VALUES('delete', old.id, old.name, old.short_description, old.description);
            INSERT INTO products_fts(rowid, name, short_description, description)
            VALUES (new.id, new.name, new.short_description, new.description);
        END;
        """)
    except sqlite3.OperationalError as e:
        # FTS5 might not be supported in some basic SQLite builds, fallback to LIKE queries if it fails
        print(f"FTS5 warning: {e}. Falling back to standard LIKE indexing.")

    # Run database migrations/schema updates safely
    migrate_db(conn)

    conn.commit()
    conn.close()

def migrate_db(conn):
    cursor = conn.cursor()
    
    # Helper to check if column exists
    def column_exists(table, column):
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        return column in columns
        
    # Helper to add column safely if missing
    def add_column_if_missing(table, column, col_type, default_val=None):
        if not column_exists(table, column):
            default_clause = f" DEFAULT {default_val}" if default_val is not None else ""
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}{default_clause};")
            print(f"[Migration] Added column {column} ({col_type}) to table {table}.")
            
    # Check and add columns across tables
    add_column_if_missing('offer_banners', 'display_order', 'INTEGER', '0')
    add_column_if_missing('products', 'updated_at', 'TIMESTAMP', 'NULL')
    add_column_if_missing('products', 'display_order', 'INTEGER', '0')
    add_column_if_missing('testimonials', 'display_order', 'INTEGER', '0')
    add_column_if_missing('video_testimonials', 'display_order', 'INTEGER', '0')
    add_column_if_missing('reviews', 'display_order', 'INTEGER', '0')
    add_column_if_missing('reviews', 'updated_at', 'TIMESTAMP', 'NULL')
    
    # Cart & Wishlist settings and analytics stats
    add_column_if_missing('settings', 'wishlist_enabled', 'INTEGER', '1')
    add_column_if_missing('settings', 'cart_enabled', 'INTEGER', '1')
    add_column_if_missing('settings', 'cart_min_value', 'REAL', '0.0')
    add_column_if_missing('settings', 'whatsapp_cart_prefix', 'TEXT', "'Hello MS Furniture Gallery, I am interested in ordering these items from my cart:'")
    add_column_if_missing('settings', 'whatsapp_wishlist_prefix', 'TEXT', "'Hello MS Furniture Gallery, here are the items in my wishlist I am interested in:'")
    add_column_if_missing('settings', 'show_facebook', 'INTEGER', '1')
    add_column_if_missing('settings', 'show_instagram', 'INTEGER', '1')
    add_column_if_missing('settings', 'show_youtube', 'INTEGER', '1')
    add_column_if_missing('settings', 'countdown_enabled', 'INTEGER', '0')
    add_column_if_missing('settings', 'countdown_end_date', 'TEXT', "''")
    add_column_if_missing('settings', 'upi_id', 'TEXT', "'9676667998@ybl'")
    add_column_if_missing('products', 'wishlist_count', 'INTEGER', '0')
    add_column_if_missing('products', 'cart_count', 'INTEGER', '0')

if __name__ == "__main__":
    init_db()
    print("Database initialised successfully.")
