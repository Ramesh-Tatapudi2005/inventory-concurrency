-- Create Products Table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    stock INTEGER NOT NULL CHECK (stock >= 0),
    version INTEGER NOT NULL DEFAULT 1
);

-- Create Orders Table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    quantity_ordered INTEGER NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial product data
INSERT INTO products (id, name, stock, version) 
VALUES (1, 'Super Widget', 100, 1)
ON CONFLICT (id) DO UPDATE SET stock = 100, version = 1;

INSERT INTO products (id, name, stock, version) 
VALUES (2, 'Mega Gadget', 50, 1)
ON CONFLICT (id) DO UPDATE SET stock = 50, version = 1;