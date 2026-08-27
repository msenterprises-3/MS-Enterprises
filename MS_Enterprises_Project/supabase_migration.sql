-- ============================================================================
-- Supabase PostgreSQL Additive Migration for MS Enterprises
-- Run this script in your Supabase Dashboard SQL Editor.
-- This script only adds missing columns and tables using IF NOT EXISTS.
-- It does NOT drop any existing tables, columns, or data.
-- ============================================================================

-- 1. Settings table missing columns
ALTER TABLE settings ADD COLUMN IF NOT EXISTS show_facebook INT DEFAULT 1;
ALTER TABLE settings ADD COLUMN IF NOT EXISTS show_instagram INT DEFAULT 1;
ALTER TABLE settings ADD COLUMN IF NOT EXISTS show_youtube INT DEFAULT 1;
ALTER TABLE settings ADD COLUMN IF NOT EXISTS countdown_enabled INT DEFAULT 0;
ALTER TABLE settings ADD COLUMN IF NOT EXISTS countdown_end_date TEXT DEFAULT '';
ALTER TABLE settings ADD COLUMN IF NOT EXISTS upi_id TEXT DEFAULT '9676667998@ybl';

-- 2. Products table missing columns
ALTER TABLE products ADD COLUMN IF NOT EXISTS dealer_status VARCHAR(50) DEFAULT 'visible';

-- 3. Dealers table missing columns
ALTER TABLE dealers ADD COLUMN IF NOT EXISTS gst_number VARCHAR(100);
ALTER TABLE dealers ADD COLUMN IF NOT EXISTS business_address TEXT;
ALTER TABLE dealers ADD COLUMN IF NOT EXISTS city VARCHAR(100);
ALTER TABLE dealers ADD COLUMN IF NOT EXISTS state VARCHAR(100);
ALTER TABLE dealers ADD COLUMN IF NOT EXISTS pincode VARCHAR(50);
ALTER TABLE dealers ADD COLUMN IF NOT EXISTS tier VARCHAR(50) DEFAULT 'default';

-- 4. Orders table missing columns
ALTER TABLE orders ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS pincode VARCHAR(50);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_notes TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_status VARCHAR(50) DEFAULT 'Pending';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_status VARCHAR(50) DEFAULT 'Pending';

-- 5. Dealer Activities table missing columns
ALTER TABLE dealer_activities ADD COLUMN IF NOT EXISTS mobile_number VARCHAR(100);

-- 6. Bulk Enquiries table missing columns
ALTER TABLE bulk_enquiries ADD COLUMN IF NOT EXISTS company VARCHAR(255);
ALTER TABLE bulk_enquiries ADD COLUMN IF NOT EXISTS details TEXT;

-- 7. Customers table (for B2C customer records)
CREATE TABLE IF NOT EXISTS customers (
    mobile_number VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    address TEXT,
    pincode VARCHAR(50),
    last_active TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
