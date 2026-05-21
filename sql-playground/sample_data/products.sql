-- E-commerce Products Sample Database

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    category_id INTEGER,
    stock INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);

INSERT INTO categories VALUES (1, 'Electronics', 'Electronic devices and gadgets');
INSERT INTO categories VALUES (2, 'Computers', 'Desktops, laptops, and tablets');
INSERT INTO categories VALUES (3, 'Accessories', 'Peripherals and add-ons');
INSERT INTO categories VALUES (4, 'Software', 'Applications and programs');

INSERT INTO products VALUES (1, 'MacBook Pro 14"', 'M3 Pro chip, 18GB RAM, 512GB SSD', 1999.00, 2, 25);
INSERT INTO products VALUES (2, 'iPhone 15 Pro', '256GB, Titanium design', 999.00, 1, 100);
INSERT INTO products VALUES (3, 'Wireless Mouse', 'Ergonomic wireless mouse', 49.99, 3, 500);
INSERT INTO products VALUES (4, 'Mechanical Keyboard', 'RGB backlit, Cherry MX switches', 129.99, 3, 150);
INSERT INTO products VALUES (5, '27" 4K Monitor', 'IPS panel, USB-C connectivity', 449.00, 1, 40);
INSERT INTO products VALUES (6, 'External SSD 1TB', 'USB 3.2, portable storage', 89.99, 3, 200);
INSERT INTO products VALUES (7, 'Webcam HD', '1080p, built-in microphone', 79.99, 3, 180);
INSERT INTO products VALUES (8, 'Office Suite', 'Word, Excel, PowerPoint, annual license', 149.99, 4, 1000);
INSERT INTO products VALUES (9, 'USB-C Hub', '7-in-1 adapter with HDMI', 59.99, 3, 300);
INSERT INTO products VALUES (10, 'Noise Canceling Headphones', 'Wireless, 30hr battery', 249.00, 1, 75);