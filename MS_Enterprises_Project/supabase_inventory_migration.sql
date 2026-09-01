-- ==============================================================================
-- Inventory Management Migration Script for Supabase (PostgreSQL)
-- Project: MS Furniture Gallery
-- ==============================================================================

-- 1. Safely add inventory management columns to the products table
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS stock_status VARCHAR(50) DEFAULT 'in_stock',
ADD COLUMN IF NOT EXISTS stock_quantity INT DEFAULT 10,
ADD COLUMN IF NOT EXISTS allow_preorder BOOLEAN DEFAULT FALSE;

-- Ensure existing product rows have valid defaults
UPDATE products 
SET stock_status = 'in_stock' 
WHERE stock_status IS NULL;

UPDATE products 
SET stock_quantity = 10 
WHERE stock_quantity IS NULL;

UPDATE products 
SET allow_preorder = FALSE 
WHERE allow_preorder IS NULL;

-- 2. Create stock_notifications table for Back in Stock notification signups
CREATE TABLE IF NOT EXISTS stock_notifications (
    id BIGSERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    contact_info VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Performance indices for rapid lookups and filtering
CREATE INDEX IF NOT EXISTS idx_stock_notifications_product_id 
ON stock_notifications(product_id);

CREATE INDEX IF NOT EXISTS idx_stock_notifications_status 
ON stock_notifications(status);

CREATE INDEX IF NOT EXISTS idx_products_stock_status 
ON products(stock_status);
