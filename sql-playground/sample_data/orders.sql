-- E-commerce Orders Sample Database

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE,
    city TEXT,
    country TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    order_date TEXT,
    total REAL,
    status TEXT DEFAULT 'pending',
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER,
    product_name TEXT,
    quantity INTEGER,
    price REAL,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

INSERT INTO customers VALUES (1, 'John', 'Smith', 'john.smith@example.com', 'New York', 'USA');
INSERT INTO customers VALUES (2, 'Jane', 'Doe', 'jane.doe@example.com', 'Los Angeles', 'USA');
INSERT INTO customers VALUES (3, 'Bob', 'Wilson', 'bob.wilson@example.com', 'Chicago', 'USA');
INSERT INTO customers VALUES (4, 'Alice', 'Brown', 'alice.brown@example.com', 'Houston', 'USA');
INSERT INTO customers VALUES (5, 'Charlie', 'Davis', 'charlie.davis@example.com', 'Phoenix', 'USA');
INSERT INTO customers VALUES (6, 'Diana', 'Miller', 'diana.miller@example.com', 'Philadelphia', 'USA');
INSERT INTO customers VALUES (7, 'Edward', 'Johnson', 'edward.johnson@example.com', 'San Antonio', 'USA');
INSERT INTO customers VALUES (8, 'Fiona', 'Garcia', 'fiona.garcia@example.com', 'San Diego', 'USA');
INSERT INTO customers VALUES (9, 'George', 'Martinez', 'george.martinez@example.com', 'Dallas', 'USA');
INSERT INTO customers VALUES (10, 'Hannah', 'Anderson', 'hannah.anderson@example.com', 'San Jose', 'USA');

INSERT INTO orders VALUES (1, 1, '2024-01-15', 129.98, 'delivered');
INSERT INTO orders VALUES (2, 2, '2024-01-16', 299.99, 'shipped');
INSERT INTO orders VALUES (3, 1, '2024-01-20', 89.99, 'processing');
INSERT INTO orders VALUES (4, 3, '2024-02-01', 549.98, 'delivered');
INSERT INTO orders VALUES (5, 4, '2024-02-05', 179.98, 'shipped');
INSERT INTO orders VALUES (6, 5, '2024-02-10', 229.99, 'pending');
INSERT INTO orders VALUES (7, 6, '2024-02-12', 399.98, 'delivered');
INSERT INTO orders VALUES (8, 7, '2024-02-15', 149.99, 'shipped');
INSERT INTO orders VALUES (9, 8, '2024-02-18', 89.99, 'processing');
INSERT INTO orders VALUES (10, 9, '2024-02-20', 699.97, 'pending');

INSERT INTO order_items VALUES (1, 1, 'Laptop', 1, 999.99);
INSERT INTO order_items VALUES (2, 1, 'Mouse', 1, 29.99);
INSERT INTO order_items VALUES (3, 2, 'Monitor', 1, 299.99);
INSERT INTO order_items VALUES (4, 3, 'Webcam', 1, 89.99);
INSERT INTO order_items VALUES (5, 4, 'Keyboard', 2, 79.99);
INSERT INTO order_items VALUES (6, 4, 'Headphones', 2, 149.99);
INSERT INTO order_items VALUES (7, 5, 'USB Cable', 2, 9.99);
INSERT INTO order_items VALUES (8, 5, 'External SSD', 1, 129.99);
INSERT INTO order_items VALUES (9, 6, 'RAM 16GB', 2, 79.99);
INSERT INTO order_items VALUES (10, 6, 'Graphics Card', 1, 499.99);