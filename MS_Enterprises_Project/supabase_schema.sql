-- Supabase PostgreSQL Schema for MS Enterprises
-- Copy and paste this script into your Supabase Dashboard SQL Editor and click RUN.

-- Drop tables if they exist (to clean up previous attempts)
DROP TABLE IF EXISTS recently_viewed_items CASCADE;
DROP TABLE IF EXISTS wishlist_items CASCADE;
DROP TABLE IF EXISTS cart_items CASCADE;
DROP TABLE IF EXISTS dealer_activities CASCADE;
DROP TABLE IF EXISTS bulk_enquiries CASCADE;
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS dealer_orders CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS dealers CASCADE;
DROP TABLE IF EXISTS category_offer_banners CASCADE;
DROP TABLE IF EXISTS category_hero_banners CASCADE;
DROP TABLE IF EXISTS video_testimonials CASCADE;
DROP TABLE IF EXISTS testimonials CASCADE;
DROP TABLE IF EXISTS trust_badges CASCADE;
DROP TABLE IF EXISTS offer_banners CASCADE;
DROP TABLE IF EXISTS hero_banners CASCADE;
DROP TABLE IF EXISTS product_variants CASCADE;
DROP TABLE IF EXISTS product_images CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS subcategories CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS catalogue_updates CASCADE;
DROP TABLE IF EXISTS settings CASCADE;

-- 1. Settings Table
CREATE TABLE settings (
    id INT PRIMARY KEY CHECK (id = 1),
    whatsapp_number VARCHAR(100) DEFAULT '+91 96766 67998',
    contact_email VARCHAR(255) DEFAULT 'info@msenterprises.com',
    contact_phone VARCHAR(100) DEFAULT '+91 96766 67998',
    contact_address TEXT,
    working_hours VARCHAR(255),
    google_map_link TEXT,
    instagram_url TEXT,
    facebook_url TEXT,
    youtube_url TEXT,
    admin_password_hash TEXT NOT NULL,
    about_story TEXT,
    about_mission TEXT,
    about_vision TEXT,
    seo_meta_title VARCHAR(255),
    seo_meta_description TEXT,
    wishlist_enabled INT DEFAULT 1,
    cart_enabled INT DEFAULT 1,
    cart_min_value NUMERIC(10,2) DEFAULT 0.0,
    whatsapp_cart_prefix TEXT,
    whatsapp_wishlist_prefix TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Categories Table
CREATE TABLE categories (
    id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    image_url TEXT,
    description TEXT,
    display_order INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active'
);

-- 3. Subcategories Table
CREATE TABLE subcategories (
    id INT PRIMARY KEY,
    category_id INT REFERENCES categories(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    display_order INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active'
);

-- 4. Products Table
CREATE TABLE products (
    id INT PRIMARY KEY,
    category_id INT REFERENCES categories(id) ON DELETE SET NULL,
    subcategory_id INT REFERENCES subcategories(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    sku VARCHAR(100),
    short_description TEXT,
    description TEXT,
    price NUMERIC(10,2),
    offer_price NUMERIC(10,2),
    offer_badge VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    is_featured INT DEFAULT 0,
    is_new_arrival INT DEFAULT 0,
    is_best_seller INT DEFAULT 0,
    is_premium INT DEFAULT 0,
    specifications JSONB,
    features JSONB,
    display_order INT DEFAULT 0,
    wishlist_count INT DEFAULT 0,
    cart_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Product Images Table
CREATE TABLE product_images (
    id INT PRIMARY KEY,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    display_order INT DEFAULT 0
);

-- 6. Product Variants Table
CREATE TABLE product_variants (
    id INT PRIMARY KEY,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    value VARCHAR(255) NOT NULL,
    price_adjustment NUMERIC(10,2) DEFAULT 0.0
);

-- 7. Hero Banners Table
CREATE TABLE hero_banners (
    id INT PRIMARY KEY,
    image_url TEXT NOT NULL,
    title VARCHAR(255),
    subtitle TEXT,
    link_text VARCHAR(100),
    link_url TEXT,
    display_order INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active'
);

-- 8. Offer Banners Table
CREATE TABLE offer_banners (
    id INT PRIMARY KEY,
    image_url TEXT NOT NULL,
    title VARCHAR(255),
    subtitle TEXT,
    ending_date VARCHAR(100),
    button_text VARCHAR(100),
    button_link TEXT,
    status VARCHAR(50) DEFAULT 'active',
    display_order INT DEFAULT 0
);

-- 9. Trust Badges Table
CREATE TABLE trust_badges (
    id INT PRIMARY KEY,
    icon_svg TEXT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    display_order INT DEFAULT 0
);

-- 10. Testimonials Table
CREATE TABLE testimonials (
    id INT PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    customer_photo TEXT,
    city VARCHAR(100),
    rating INT DEFAULT 5,
    review TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    display_order INT DEFAULT 0
);

-- 11. Video Testimonials Table
CREATE TABLE video_testimonials (
    id INT PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    video_url TEXT NOT NULL,
    thumbnail_url TEXT,
    review_text TEXT,
    status VARCHAR(50) DEFAULT 'active',
    display_order INT DEFAULT 0
);

-- 12. Category Hero Banners Table
CREATE TABLE category_hero_banners (
    id INT PRIMARY KEY,
    category_id INT REFERENCES categories(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    title VARCHAR(255),
    button_text VARCHAR(100) DEFAULT 'Explore Collection',
    offer_text VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active'
);

-- 13. Category Offer Banners Table
CREATE TABLE category_offer_banners (
    id INT PRIMARY KEY,
    category_id INT REFERENCES categories(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    title VARCHAR(255),
    product_image_url TEXT,
    product_price NUMERIC(10,2),
    discount VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active'
);

-- 14. Catalogue Updates Table
CREATE TABLE catalogue_updates (
    id INT PRIMARY KEY CHECK (id = 1),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 15. Dealers Table
CREATE TABLE dealers (
    id VARCHAR(100) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    business_name VARCHAR(255),
    dealer_name VARCHAR(255),
    mobile_number VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 16. Orders Table (B2C Checkouts)
CREATE TABLE orders (
    id VARCHAR(100) PRIMARY KEY,
    session_id VARCHAR(255),
    mobile_number VARCHAR(100),
    total_value NUMERIC(10,2),
    status VARCHAR(50) DEFAULT 'pending',
    payment_method VARCHAR(100),
    items_json TEXT,
    customer_name VARCHAR(255),
    shipping_address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 17. Dealer Orders Table (B2B Checkouts)
CREATE TABLE dealer_orders (
    id VARCHAR(100) PRIMARY KEY,
    dealer_id VARCHAR(100) REFERENCES dealers(id) ON DELETE SET NULL,
    business_name VARCHAR(255),
    total_value NUMERIC(10,2),
    status VARCHAR(50) DEFAULT 'pending',
    items_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 18. Cart Items Table
CREATE TABLE cart_items (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    product_id VARCHAR(100) NOT NULL,
    quantity INT DEFAULT 1,
    variant_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 19. Wishlist Items Table
CREATE TABLE wishlist_items (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    product_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, product_id)
);

-- 20. Recently Viewed Items Table
CREATE TABLE recently_viewed_items (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    product_id VARCHAR(100) NOT NULL,
    viewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, product_id)
);

-- 21. Reviews Table
CREATE TABLE reviews (
    id VARCHAR(100) PRIMARY KEY,
    product_id VARCHAR(100),
    reviewer_name VARCHAR(255) NOT NULL,
    rating INT NOT NULL,
    review_text TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    display_order INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
);

-- 22. Dealer Activities Table
CREATE TABLE dealer_activities (
    id VARCHAR(255) PRIMARY KEY,
    dealer_id VARCHAR(100),
    dealer_name VARCHAR(255),
    business_name VARCHAR(255),
    action VARCHAR(255),
    details TEXT,
    device VARCHAR(255),
    ip_address VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 23. Bulk Enquiries Table
CREATE TABLE bulk_enquiries (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(100),
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
