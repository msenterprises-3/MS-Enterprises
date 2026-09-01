import os
import sqlite3
import json
import random
import re
from werkzeug.security import generate_password_hash
from database import get_db_connection, init_db

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\-]', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def seed():
    # Make sure tables exist
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing data to prevent duplicates
    cursor.execute("DELETE FROM reviews;")
    cursor.execute("DELETE FROM video_testimonials;")
    cursor.execute("DELETE FROM testimonials;")
    cursor.execute("DELETE FROM trust_badges;")
    cursor.execute("DELETE FROM offer_banners;")
    cursor.execute("DELETE FROM hero_banners;")
    cursor.execute("DELETE FROM product_variants;")
    cursor.execute("DELETE FROM product_images;")
    cursor.execute("DELETE FROM products;")
    cursor.execute("DELETE FROM subcategories;")
    cursor.execute("DELETE FROM categories;")
    cursor.execute("DELETE FROM settings;")

    # Seed Settings
    default_pw_hash = generate_password_hash("MSEnterprises2026")
    cursor.execute("""
    INSERT INTO settings (id, whatsapp_number, contact_email, contact_phone, contact_address, working_hours, google_map_link, instagram_url, facebook_url, youtube_url, admin_password_hash, about_story, about_mission, about_vision, seo_meta_title, seo_meta_description)
    VALUES (1, '+91 96766 67998', 'msfurnitureglry@gmail.com', '+91 96766 67998', 'MS Enterprises\nMain Road, Beside TSR Function Hall,\nMannuru, Rajampet,\nAndhra Pradesh – 516126', '10:00 AM - 08:30 PM (Mon-Sun)', 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3844.8239088619623!2d79.16010537484433!3d14.19502759006059!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3bb2b2ba119cbf41%3A0xf7de7a0e3f169f4c!2sTSR%20Kalyanamandapam!5e0!3m2!1sen!2sin!4v1700000000000', 'https://www.instagram.com/msenterprises.rjp?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw==', 'https://facebook.com/msenterprises', 'https://youtube.com/msenterprises', ?, 
    'MS Enterprises has been the pioneer of luxury home styling since 2012. We bring curated luxury furniture from across the globe directly to your home at unbeatable prices. From solid wood classics to contemporary modular marvels, we design and source our catalogs with an eye for exceptional quality and comfort.',
    'To offer high-end, premium quality furniture solutions that elevate Indian homes, making international standards accessible without custom duties or complex import pipelines.',
    'To build India''s most trusted and direct-to-customer furniture and home lifestyle catalog brand, powered by instant WhatsApp communication.',
    'Premium Home & Office Furniture Catalogue | MS Enterprises',
    'Explore MS Enterprises'' exclusive furniture collection. Premium beds, sofas, dining tables, and office setups. Order directly on WhatsApp.');
    """, (default_pw_hash,))

    # Seed Categories
    categories_data = [
        ("Sofas", "sofas", "/static/uploads/cat_sofas.webp", "Luxury fabric, leatherette, and solid wood sofas."),
        ("Beds", "beds", "/static/uploads/cat_beds.webp", "Premium king and queen sized beds with storage solutions."),
        ("Dining Sets", "dining-sets", "/static/uploads/cat_dining.webp", "Elegant dining tables with ergonomic chairs."),
        ("Office Furniture", "office-furniture", "/static/uploads/cat_office.webp", "Productive desks, luxury chairs, and storage options."),
        ("Wardrobes", "wardrobes", "/static/uploads/cat_wardrobes.webp", "Spacious 2, 3, and 4-door modular wardrobes."),
        ("Tables", "tables", "/static/uploads/cat_tables.webp", "Coffee tables, side tables, and console tables."),
        ("Chairs", "chairs", "/static/uploads/cat_chairs.webp", "Accent chairs, recliners, and study chairs."),
        ("Decor & Lighting", "decor-lighting", "/static/uploads/cat_decor.webp", "Lamps, wall art, and premium home decors."),
        ("Storage Cabinets", "storage-cabinets", "/static/uploads/cat_storage.webp", "Sideboards, shoe racks, and book shelves."),
        ("Mattresses", "mattresses", "/static/uploads/cat_mattresses.webp", "Orthopedic, memory foam, and latex pocket spring mattresses."),
        ("Outdoor Furniture", "outdoor-furniture", "/static/uploads/cat_outdoor.webp", "All-weather garden sets, swings, and loungers."),
        ("Home Office", "home-office", "/static/uploads/cat_home_office.webp", "Compact tables and comfortable chairs for work-from-home.")
    ]

    cat_id_map = {}
    for name, slug, img, desc in categories_data:
        cursor.execute("INSERT INTO categories (name, slug, image_url, description) VALUES (?, ?, ?, ?)", (name, slug, img, desc))
        cat_id_map[slug] = cursor.lastrowid

    # Seed Subcategories
    subcategories_data = {
        "sofas": [("1 Seater Sofas", "1-seater-sofas"), ("2 Seater Sofas", "2-seater-sofas"), ("3 Seater Sofas", "3-seater-sofas"), ("L-Shape Sofas", "l-shape-sofas"), ("Recliners", "recliners")],
        "beds": [("King Size Beds", "king-size-beds"), ("Queen Size Beds", "queen-size-beds"), ("Beds with Storage", "beds-with-storage"), ("Hydraulic Beds", "hydraulic-beds")],
        "dining-sets": [("4 Seater Dining Sets", "4-seater-dining-sets"), ("6 Seater Dining Sets", "6-seater-dining-sets"), ("8 Seater Dining Sets", "8-seater-dining-sets"), ("Marble Dining Tables", "marble-dining-tables")],
        "office-furniture": [("Office Chairs", "office-chairs"), ("Executive Desks", "executive-desks"), ("Filing Cabinets", "filing-cabinets"), ("Conference Tables", "conference-tables")],
        "wardrobes": [("2 Door Wardrobes", "2-door-wardrobes"), ("3 Door Wardrobes", "3-door-wardrobes"), ("4 Door Wardrobes", "4-door-wardrobes"), ("Sliding Wardrobes", "sliding-wardrobes")],
        "tables": [("Coffee Tables", "coffee-tables"), ("Side Tables", "side-tables"), ("Console Tables", "console-tables"), ("TV Units", "tv-units")],
        "chairs": [("Accent Chairs", "accent-chairs"), ("Recliner Chairs", "recliner-chairs"), ("Study Chairs", "study-chairs"), ("Stools & Poufs", "stools-poufs")],
        "decor-lighting": [("Table Lamps", "table-lamps"), ("Floor Lamps", "floor-lamps"), ("Wall Art", "wall-art"), ("Vases", "vases")],
        "storage-cabinets": [("Sideboards", "sideboards"), ("Shoe Racks", "shoe-racks"), ("Book Shelves", "book-shelves"), ("Crockery Units", "crockery-units")],
        "mattresses": [("Memory Foam", "memory-foam-mattresses"), ("Pocket Spring", "pocket-spring-mattresses"), ("Orthopedic", "orthopedic-mattresses")],
        "outdoor-furniture": [("Balcony Sets", "balcony-sets"), ("Garden Swings", "garden-swings"), ("Loungers", "loungers")],
        "home-office": [("Study Desks", "study-desks"), ("Ergonomic Office Chairs", "ergonomic-office-chairs")]
    }

    subcat_id_map = {}
    for cat_slug, subcats in subcategories_data.items():
        cat_id = cat_id_map[cat_slug]
        subcat_id_map[cat_slug] = []
        for sname, sslug in subcats:
            cursor.execute("INSERT INTO subcategories (category_id, name, slug) VALUES (?, ?, ?)", (cat_id, sname, sslug))
            subcat_id_map[cat_slug].append((sslug, cursor.lastrowid))

    # Seed Hero Banners
    hero_banners = [
        ("/static/uploads/hero_banner1.webp", "Elevate Your Living Experience", "Explore our premium handcrafted solid teak wood furniture catalog.", "Explore Catalogue", "/products"),
        ("/static/uploads/hero_banner2.webp", "Luxury Bedroom Collection", "Indulge in comfort with our modular king size hydraulic storage beds.", "View Beds", "/products?category=beds"),
        ("/static/uploads/hero_banner3.webp", "Work From Home In Style", "Ergonomically designed office chairs and space-saving study desks.", "Shop Office", "/products?category=office-furniture")
    ]
    for img, title, sub, btn_text, btn_link in hero_banners:
        cursor.execute("INSERT INTO hero_banners (image_url, title, subtitle, link_text, link_url) VALUES (?, ?, ?, ?, ?)", (img, title, sub, btn_text, btn_link))

    # Seed Offer Banners
    offer_banners = [
        ("/static/uploads/offer_festive.webp", "Festive Home Makeover", "Get up to 40% off on premium dining table sets and recliners. Limited stock.", "2026-10-31 23:59:59", "Order Now", "/products?featured=best-seller")
    ]
    for img, title, sub, end_dt, btn_txt, btn_lnk in offer_banners:
        cursor.execute("INSERT INTO offer_banners (image_url, title, subtitle, ending_date, button_text, button_link) VALUES (?, ?, ?, ?, ?, ?)", (img, title, sub, end_dt, btn_txt, btn_lnk))

    # Seed Trust Badges
    trust_badges = [
        ("award", "Premium Quality", "Crafted from handpicked premium grade woods and materials."),
        ("indian-rupee", "Best Prices", "Direct from factory prices, avoiding middlemen commissions."),
        ("grid", "1000+ Products", "A wide variety of designs to suit every style preference."),
        ("truck", "Fast Delivery", "Safe transit and professional assembly at your doorstep."),
        ("smile", "Customer First", "Dedicated customer support and direct updates on WhatsApp."),
        ("phone-call", "WhatsApp Order", "Direct ordering bypasses complex checkout panels.")
    ]
    for icon, title, desc in trust_badges:
        cursor.execute("INSERT INTO trust_badges (icon_svg, title, description) VALUES (?, ?, ?)", (icon, title, desc))

    # Seed Testimonials
    testimonials = [
        ("Naveen Kumar Guntimadugu", "/static/uploads/test_user1.webp", "Rajampet", 5, "One of the most affordable and good quality furniture stores in Rajampet. Very happy with the purchase. Friendly staff and excellent behaviour. Highly recommended!"),
        ("Sajid Saju", "/static/uploads/test_user2.webp", "Rajampet", 5, "We visited the store and purchased a cot and sofa. The staff guided us very well. The products are of excellent quality at very reasonable prices. Completely satisfied."),
        ("Raja Sekhar", "/static/uploads/test_user3.webp", "Rajampet", 5, "Best furniture at affordable prices. I am fully satisfied with the product quality and the quick response from MS Enterprises."),
        ("Anil Kumar", "/static/uploads/test_user4.webp", "Rajampet", 5, "Purchased a king-size cot. Very good quality with a reasonable price. Excellent workmanship and timely delivery.")
    ]
    for name, img, city, rating, review in testimonials:
        cursor.execute("INSERT INTO testimonials (customer_name, customer_photo, city, rating, review) VALUES (?, ?, ?, ?, ?)", (name, img, city, rating, review))

    # Seed Video Testimonials
    video_testimonials = [
        ("Rahul Verma", "https://www.youtube.com/embed/dQw4w9WgXcQ", "/static/uploads/vid_thumb1.webp", "Customer walk-through of the newly installed Modular Wardrobe in Gachibowli, Hyderabad."),
        ("Sneha Patil", "https://www.youtube.com/embed/dQw4w9WgXcQ", "/static/uploads/vid_thumb2.webp", "Review of the 3+2 Luxury Recliner Sofa set in Jubilee Hills.")
    ]
    for name, url, thumb, txt in video_testimonials:
        cursor.execute("INSERT INTO video_testimonials (customer_name, video_url, thumbnail_url, review_text) VALUES (?, ?, ?, ?)", (name, url, thumb, txt))

    # Define realistic product data templates to seed details
    sofa_adjectives = ["Italian Leatherette", "Chesterfield Fabric", "L-Shaped Sectional", "Classic Wingback", "Ergonomic Manual Recliner", "Solid Wood Frame Lounge"]
    bed_adjectives = ["Hydraulic Storage Modular", "Upholstered Wingback", "Classic Sheesham Wood", "Premium Teakwood Poster", "Low-Profile Platform", "Plush Headboard Panel"]
    dining_adjectives = ["6-Seater Italian Marble", "4-Seater Compact Glass Top", "8-Seater Grand Royal Teak", "Contemporary Ceramic Top", "Solid Rosewood Minimalist", "Nordic Round Dining Table"]
    office_adjectives = ["High-Back Mesh Ergonomic", "Luxury Leather Boss", "Space-Saving Corner study", "Executive Mahogany Veneer", "Adjustable Height Stand-up", "Modular Workstation Desk"]
    wardrobe_adjectives = ["3-Door Sliding Mirror", "4-Door Classic Matte Finish", "2-Door High-Gloss Compact", "Walk-in Wardrobe System", "Solid Pine Wood Wardrobe", "Modular Dressing Unit"]

    materials = ["Teak Wood", "Sheesham Wood", "Rosewood", "Engineered Wood", "High-Grade Metal", "Italian Marble", "Premium Fabric", "Genuine Leatherette"]
    colors = ["Imperial Walnut", "Royal Oak", "Mahogany Dark", "Charcoal Gray", "Beige Gold", "Classic Tan", "Nordic White", "Forest Green"]

    spec_templates = {
        "sofas": {
            "Material": ["Solid Teak Frame + High Density Foam", "Eucalyptus Wood + Velvet Fabric", "Solid Wood Frame + Premium Leatherette"],
            "Seating Capacity": ["3 Seater", "2 Seater", "5 Seater (3+1+1)", "L-Shape 6 Seater"],
            "Cushion Type": ["Pocket Spring + 32 Density PU Foam", "Super Soft High Density HR Foam"],
            "Warranty": ["3 Years Frame & Foam Warranty", "5 Years Structural Warranty"],
            "Dimensions": ["80 x 36 x 34 inches", "92 x 38 x 36 inches", "110 x 65 x 35 inches"]
        },
        "beds": {
            "Material": ["Premium Engineered Wood with Glossy Laminate", "Solid Sheesham Wood", "Teak Wood + Fabric Tufted Headboard"],
            "Size": ["King Size (72 x 78 inches mattress size)", "Queen Size (60 x 78 inches mattress size)"],
            "Storage Type": ["Hydraulic Gas-Lift Storage", "Manual Drawer Storage", "No Storage"],
            "Headboard Style": ["Tufted Velvet Cushioning", "Solid Wooden Panel", "Geometric Wooden Inlay"],
            "Warranty": ["5 Years Termite and Structural Warranty", "3 Years Wood Warranty"]
        },
        "dining-sets": {
            "Table Top Material": ["15mm Thick Italian Onyx Marble", "Solid Teak Wood", "Tempered Safety Glass"],
            "Chair Material": ["Rubberwood with Fabric Seat Cushion", "Teak Wood with PU Leatherette"],
            "Seating Capacity": ["4 Seater", "6 Seater", "8 Seater"],
            "Table Dimensions": ["60 x 36 x 30 inches", "72 x 40 x 30 inches", "48 x 48 x 30 inches"],
            "Warranty": ["1 Year Table and Chair Structural Warranty", "3 Years Warranty"]
        },
        "office-furniture": {
            "Chair Mechanism": ["Synchro Tilt Lock Mechanism", "Knee-Tilt Multi Lock", "Simple Center-Tilt"],
            "Desk Material": ["Pre-laminated Particle Board with Powder Coated Steel Frame", "Solid Wood top with Metal Frame"],
            "Adjustability": ["Pneumatic Height Adjustment + 3D Armrest", "Height Adjustment Only"],
            "Warranty": ["2 Years Warranty on gas lift & wheels", "1 Year Desk Warranty"]
        }
    }

    feature_templates = [
        "Crafted by master artisans with attention to detail",
        "Reinforced joints for exceptional structural stability",
        "Ergonomically designed for absolute comfort during prolonged use",
        "Treated against termites, wood-borers, and environmental moisture",
        "Premium multi-layered lacquer/polish for a long-lasting premium shine",
        "Easy to clean fabric/surface requiring minimal periodic maintenance",
        "Modular design allows convenient dismantling and reallocation"
    ]

    print("Generating products...")

    product_count = 0
    # Seed 20 detailed "Real" products first, to show beautiful realistic data on home and first pages
    real_products = [
        # Sofas
        ("MS Royal Oak Premium 3-Seater Sofa", "sofas", "3-seater-sofas", 34999, 29999, "15% OFF", 1, 1, 0, 1,
         "Transform your living room with this classic Royal Oak styling 3-seater sofa. Built with a solid teak frame and premium beige gold fabric.",
         "This majestic 3-seater sofa features deep diamond tufting and curved armrests inspired by timeless Chesterfield designs. The seat cushions are packed with pocket springs and 32-density foam for unmatched seating comfort. Accented with brass stud details and solid wood turned legs, it brings an instant touch of class to any modern or traditional home living area.",
         ["Solid Teakwood Frame", "Premium Velvet Fabric", "3 Seater", "Pocket Spring + PU Foam", "84 x 38 x 35 inches", "3 Years Frame Warranty"]),
        
        ("MS Emperor L-Shape Leatherette Sofa", "sofas", "l-shape-sofas", 65000, 54999, "Hot Deal", 1, 0, 1, 1,
         "Elegant charcoal gray L-shape sectional sofa, perfect for luxury lounge seating. Upholstered in premium scratch-resistant leatherette.",
         "Designed for modern homes, the MS Emperor Sectional Sofa features a versatile reversible chaise longue. Its high-back cushions offer superior neck support, and the easy-to-clean leatherette is perfect for households with pets or children. Solid hardwood frame ensures zero sagging over years of usage.",
         ["Solid Wood + Plywood Frame", "Scratch-resistant Leatherette", "5-6 Seater Sectional", "High Resilience HR Foam", "110 x 68 x 36 inches", "5 Years Structural Warranty"]),
        
        ("MS Cloud Ergonomic Recliner Chair", "sofas", "recliners", 22000, 17999, "New", 0, 1, 1, 0,
         "Indulge in absolute comfort. Single-seater manual recliner with premium tan fabric upholstery and three-position reclining mechanism.",
         "Sit back and unwind. The MS Cloud Recliner is ergonomically contoured to cradle your spine. Features a robust iron frame recliner mechanism and premium heavy-duty microfiber fabric. Includes integrated cup holders and side pockets for holding books or remote controllers.",
         ["Metal Reclining Frame", "Microfiber Fabric", "1 Seater Recliner", "Sinuous Springs + Memory Foam Overlay", "36 x 38 x 40 inches", "2 Years Recliner Mechanism Warranty"]),

        # Beds
        ("MS Grand Heritage Hydraulic Storage Bed", "beds", "king-size-beds", 48000, 39999, "Popular", 1, 1, 1, 1,
         "Solid Sheesham wood king-size bed with smooth hydraulic gas lift storage. Beautiful natural wood grain finish.",
         "Make a bold statement with the MS Grand Heritage Bed. Crafted from seasoned Sheesham wood (Indian Rosewood), it showcases a rustic headboard panel with horizontal slats. The dual hydraulic gas-lift mechanism gives you access to a huge storage box beneath the mattress frame, making seasonal storage easy and dust-free.",
         ["Seasoned Sheesham Wood", "King Size (72x78 inches)", "Dual Gas-Lift Hydraulic Storage", "Natural Honey Oak Finish", "82 x 76 x 42 inches", "5 Years Termite Warranty"]),
         
        ("MS Velvet Crown Tufted Queen Bed", "beds", "queen-size-beds", 38000, 32000, "15% OFF", 0, 1, 0, 0,
         "Premium modular queen size bed with a luxurious emerald green velvet tufted headboard. Includes drawer storage.",
         "Bring luxury hotel vibes into your master bedroom. The MS Velvet Crown bed features a towering headboard with deep diamond button tuftings. Structurally built with thick engineered MDF boards and supported by steel crossbeams. Equipped with four spacious pull-out drawer boxes at the base for organization.",
         ["Premium MDF + Fabric Headboard", "Queen Size (60x78 inches)", "4 Drawer Storage", "Emerald Green Velvet Upholstery", "80 x 64 x 48 inches", "3 Years Structural Warranty"]),

        # Dining Sets
        ("MS Majestic Italian Marble 6-Seater Dining Set", "dining-sets", "6-seater-dining-sets", 78000, 68000, "Best Seller", 1, 0, 1, 1,
         "Ultra-luxurious dining set featuring a 15mm thick white Italian marble table top and 6 matching teak wood upholstered chairs.",
         "Dine like royalty. The MS Majestic Dining Set showcases an exquisite white Carrara marble top with gray veining, double-coated for stain and heat protection. The tabletop sits on a designer solid wood trestle base. Accompanied by 6 chairs upholstered in premium stain-proof gray fabric, contoured for optimal back support.",
         ["Italian Carrara Marble + Teak wood legs", "6 Seater Dining Set", "Double Coated Polished Marble", "60 x 38 x 30 inches (Table)", "5 Years Table Base Warranty"]),

        # Office Furniture
        ("MS ErgoPro High-Back Office Chair", "office-furniture", "office-chairs", 12999, 8999, "Best Price", 1, 1, 1, 0,
         "Premium ergonomic mesh chair for home office or corporate setups. Complete adjustment features for back and arm support.",
         "Stay productive and pain-free. The MS ErgoPro features a highly breathable mesh back, adjustable lumbar support pad, 3D armrests (height, depth, angle), synchro tilt-lock mechanism, and heavy-duty nylon wheels. Perfect for sitting comfortably during long 8-10 hour work shifts.",
         ["High-tensile Korean Mesh + Metal Base", "Executive Ergonomic Office Chair", "Synchro Tilt Lock + 3D Arms", "Class 4 Gas Lift (150kg limit)", "26 x 26 x 48-52 inches", "2 Years Wheels & Gas Lift Warranty"]),
         
        ("MS Senator Executive Mahogany Desk", "office-furniture", "executive-desks", 28000, 22999, "Premium", 0, 0, 0, 1,
         "Commanding executive study desk finished in premium mahogany wood veneer. Includes side return credenza storage.",
         "The perfect centerpiece for a home office or corporate cabin. Crafted with a premium mahogany polish and a leatherette writing pad inlay. Features an L-shaped side return desk housing multiple drawers, CPU cabinet, and keyboard slider. Equipped with wire grommet caps for clean cable management.",
         ["MDF with Teak/Mahogany Veneer", "Executive Writing Desk with Credenza", "Matte Mahogany Polish", "60 x 30 x 30 inches (Main Desk)", "3 Years Structural Warranty"])
    ]

    for name, cat_slug, subcat_slug, orig_price, off_price, badge, feat, new_arr, best, premium, short_desc, desc, specs_list in real_products:
        cat_id = cat_id_map[cat_slug]
        subcat_id = None
        for s_slug, s_id in subcat_id_map[cat_slug]:
            if s_slug == subcat_slug:
                subcat_id = s_id
                break
        
        slug = slugify(name)
        
        # Build specifications dictionary
        specs = {}
        for spec_item in specs_list:
            if "Warranty" in spec_item:
                specs["Warranty"] = spec_item
            elif "Dimensions" in spec_item or "Size" in spec_item:
                specs["Dimensions"] = spec_item
            elif "Material" in spec_item:
                specs["Material"] = spec_item
            else:
                parts = spec_item.split(" ", 1)
                specs[parts[0]] = spec_item

        features = [
            "Premium grade build inspired by RoyalOak luxury catalogs.",
            "Treated wood construction preventing expansion/contraction due to weather.",
            "Direct-to-WhatsApp delivery pipeline across South India.",
            "Secure assembly carried out by professional technical staff."
        ]

        cursor.execute("""
        INSERT INTO products (category_id, subcategory_id, name, slug, sku, short_description, description, price, offer_price, offer_badge, status, is_featured, is_new_arrival, is_best_seller, is_premium, specifications, features)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?)
        """, (cat_id, subcat_id, name, slug, f"MSE-{random.randint(10000, 99999)}", short_desc, desc, orig_price, off_price, badge, feat, new_arr, best, premium, json.dumps(specs), json.dumps(features)))
        
        prod_id = cursor.lastrowid
        
        # Seed images
        cursor.execute("INSERT INTO product_images (product_id, image_url, display_order) VALUES (?, ?, 0)", (prod_id, f"/static/uploads/prod_{slug}_1.webp"))
        cursor.execute("INSERT INTO product_images (product_id, image_url, display_order) VALUES (?, ?, 1)", (prod_id, f"/static/uploads/prod_{slug}_2.webp"))
        cursor.execute("INSERT INTO product_images (product_id, image_url, display_order) VALUES (?, ?, 2)", (prod_id, f"/static/uploads/prod_{slug}_3.webp"))
        
        # Add simple variant
        cursor.execute("INSERT INTO product_variants (product_id, name, value, price_adjustment) VALUES (?, 'Primary Material', 'Teak Wood', 0.0)", (prod_id,))
        cursor.execute("INSERT INTO product_variants (product_id, name, value, price_adjustment) VALUES (?, 'Primary Material', 'Sheesham Wood', 5000.0)", (prod_id,))
        
        product_count += 1

    # Now loop to generate the remaining ~992 products so we have over 1000 products total!
    # We will generate products across the 12 categories.
    print("Generating bulk products...")
    
    category_slugs = list(cat_id_map.keys())
    
    bulk_product_idx = 1
    
    while product_count < 1010:
        cat_slug = random.choice(category_slugs)
        cat_id = cat_id_map[cat_slug]
        subcats = subcat_id_map[cat_slug]
        
        subcat_slug, subcat_id = random.choice(subcats)
        
        # Pick adjectives based on category
        adj = ""
        if cat_slug == "sofas":
            adj = random.choice(sofa_adjectives)
        elif cat_slug == "beds":
            adj = random.choice(bed_adjectives)
        elif cat_slug == "dining-sets":
            adj = random.choice(dining_adjectives)
        elif cat_slug == "office-furniture":
            adj = random.choice(office_adjectives)
        elif cat_slug == "wardrobes":
            adj = random.choice(wardrobe_adjectives)
        else:
            adj = random.choice(["Premium Classic", "Luxury Modular", "Royal Antique", "Modern Designer", "Handcrafted Solid", "Contemporary Elite"])
            
        mat = random.choice(materials)
        col = random.choice(colors)
        
        prod_name = f"MS {adj} {mat} ({col}) - {bulk_product_idx}"
        slug = slugify(prod_name)
        
        sku = f"MSE-{random.randint(100000, 999999)}"
        short_desc = f"Luxury {cat_slug.replace('-', ' ')} crafted from top-tier {mat} in a premium {col} finish."
        desc = f"Experience the absolute zenith of luxury with the {prod_name}. Masterfully assembled using prime quality {mat} selection, treated for protection against pests, humidity, and wear. Features an ergonomically engineered footprint, making it the perfect focal statement for your premium home setup. Part of MS Enterprises' limited signature catalog series."
        
        # Set realistic prices
        base_price = random.randint(1500, 12000) * 10
        if cat_slug in ["sofas", "beds", "dining-sets"]:
            base_price = random.randint(25000, 95000)
            
        discount = random.choice([0, 10, 15, 20, 25])
        orig_price = base_price
        
        if discount > 0:
            off_price = int(orig_price * (1 - (discount / 100)))
            badge = f"{discount}% OFF"
        else:
            off_price = None
            badge = random.choice([None, "New Launch", "Hot Seller"])
            
        is_feat = random.choice([0, 0, 0, 1])
        is_new = random.choice([0, 0, 1, 0])
        is_best = random.choice([0, 0, 0, 1])
        is_prem = random.choice([0, 0, 0, 0, 1])
        
        # specs
        specs = {
            "Material": f"{mat} with {col} polish finish",
            "Dimensions": f"{random.randint(30, 90)} x {random.randint(20, 60)} x {random.randint(15, 45)} inches",
            "Warranty": f"{random.choice([1, 2, 3, 5])} Years Structural Warranty",
            "SKU": sku
        }
        
        # Add custom category specs if available
        if cat_slug in spec_templates:
            for k, v in spec_templates[cat_slug].items():
                specs[k] = random.choice(v)
                
        features = [random.choice(feature_templates) for _ in range(3)]
        features.append("Factory direct pricing bypasses luxury offline stores.")
        
        cursor.execute("""
        INSERT INTO products (category_id, subcategory_id, name, slug, sku, short_description, description, price, offer_price, offer_badge, status, is_featured, is_new_arrival, is_best_seller, is_premium, specifications, features)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?)
        """, (cat_id, subcat_id, prod_name, slug, sku, short_desc, desc, orig_price, off_price, badge, is_feat, is_new, is_best, is_prem, json.dumps(specs), json.dumps(features)))
        
        prod_id = cursor.lastrowid
        
        # Single image for bulk products to save space
        cursor.execute("INSERT INTO product_images (product_id, image_url, display_order) VALUES (?, ?, 0)", (prod_id, f"/static/uploads/products/prod_generic_{random.randint(1, 4)}.webp"))
        
        product_count += 1
        bulk_product_idx += 1

    conn.commit()
    conn.close()
    print(f"Database seeded successfully with {product_count} products.")

if __name__ == "__main__":
    seed()
