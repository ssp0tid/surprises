-- Chinook Music Store Sample Database

CREATE TABLE IF NOT EXISTS artists (
    artist_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS albums (
    album_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    artist_id INTEGER,
    year INTEGER,
    FOREIGN KEY (artist_id) REFERENCES artists(artist_id)
);

CREATE TABLE IF NOT EXISTS tracks (
    track_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    album_id INTEGER,
    milliseconds INTEGER,
    bytes INTEGER,
    unit_price REAL,
    FOREIGN KEY (album_id) REFERENCES albums(album_id)
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT,
    country TEXT,
    city TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    invoice_date TEXT,
    total REAL,
    billing_address TEXT,
    billing_city TEXT,
    billing_country TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS invoice_items (
    item_id INTEGER PRIMARY KEY,
    invoice_id INTEGER,
    track_id INTEGER,
    quantity INTEGER,
    unit_price REAL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
    FOREIGN KEY (track_id) REFERENCES tracks(track_id)
);

-- Insert Artists
INSERT INTO artists VALUES (1, 'AC/DC');
INSERT INTO artists VALUES (2, 'Led Zeppelin');
INSERT INTO artists VALUES (3, 'Metallica');
INSERT INTO artists VALUES (4, 'The Rolling Stones');
INSERT INTO artists VALUES (5, 'U2');
INSERT INTO artists VALUES (6, 'Pink Floyd');
INSERT INTO artists VALUES (7, 'Queen');
INSERT INTO artists VALUES (8, 'The Beatles');
INSERT INTO artists VALUES (9, ' Guns N'' Roses');
INSERT INTO artists VALUES (10, 'Deep Purple');

-- Insert Albums
INSERT INTO albums VALUES (1, 'For Those About to Rock', 1, 1981);
INSERT INTO albums VALUES (2, 'Physical Graffiti', 2, 1975);
INSERT INTO albums VALUES (3, 'Master of Puppets', 3, 1986);
INSERT INTO albums VALUES (4, 'Some Girls', 4, 1978);
INSERT INTO albums VALUES (5, 'The Joshua Tree', 5, 1987);
INSERT INTO albums VALUES (6, 'The Dark Side of the Moon', 6, 1973);
INSERT INTO albums VALUES (7, 'A Night at the Opera', 7, 1975);
INSERT INTO albums VALUES (8, 'Abbey Road', 8, 1969);
INSERT INTO albums VALUES (9, 'Appetite for Destruction', 9, 1987);
INSERT INTO albums VALUES (10, 'Machine Head', 10, 1972);

-- Insert Tracks
INSERT INTO tracks VALUES (1, 'For Those About to Rock', 1, 343719, 11170042, 0.99);
INSERT INTO tracks VALUES (2, 'Spellbound', 1, 253210, 8224804, 0.99);
INSERT INTO tracks VALUES (3, 'Kashmir', 2, 523328, 17021658, 0.99);
INSERT INTO tracks VALUES (4, 'Trampled Under Foot', 2, 337837, 11073990, 0.99);
INSERT INTO tracks VALUES (5, 'Battery', 3, 302530, 9866910, 0.99);
INSERT INTO tracks VALUES (6, 'Master of Puppets', 3, 403319, 13199770, 0.99);
INSERT INTO tracks VALUES (7, 'Miss You', 4, 261049, 8503464, 0.99);
INSERT INTO tracks VALUES (8, 'Shattered', 4, 244590, 7991819, 0.99);
INSERT INTO tracks VALUES (9, 'Where the Streets Have No Name', 5, 300552, 9824468, 0.99);
INSERT INTO tracks VALUES (10, 'I Still Haven''t Found What I''m Looking For', 5, 277580, 9060628, 0.99);
INSERT INTO tracks VALUES (11, 'Time', 6, 413624, 13181620, 0.99);
INSERT INTO tracks VALUES (12, 'Money', 6, 382615, 12605970, 0.99);
INSERT INTO tracks VALUES (13, 'Bohemian Rhapsody', 7, 354320, 11511708, 0.99);
INSERT INTO tracks VALUES (14, 'Love of My Life', 7, 205739, 6618706, 0.99);
INSERT INTO tracks VALUES (15, 'Come Together', 8, 259624, 8514972, 0.99);
INSERT INTO tracks VALUES (16, 'Here Comes the Sun', 8, 187136, 6105296, 0.99);
INSERT INTO tracks VALUES (17, 'Welcome to the Jungle', 9, 273792, 8968456, 0.99);
INSERT INTO tracks VALUES (18, 'Sweet Child o'' Mine', 9, 356493, 11642868, 0.99);
INSERT INTO tracks VALUES (19, 'Smoke on the Water', 10, 337780, 11011082, 0.99);
INSERT INTO tracks VALUES (20, 'Highway Star', 10, 363896, 11888504, 0.99);

-- Insert Customers
INSERT INTO customers VALUES (1, 'John', 'Smith', 'john.smith@example.com', 'USA', 'New York');
INSERT INTO customers VALUES (2, 'Jane', 'Doe', 'jane.doe@example.com', 'Canada', 'Toronto');
INSERT INTO customers VALUES (3, 'Bob', 'Wilson', 'bob.wilson@example.com', 'UK', 'London');
INSERT INTO customers VALUES (4, 'Alice', 'Brown', 'alice.brown@example.com', 'Australia', 'Sydney');
INSERT INTO customers VALUES (5, 'Charlie', 'Davis', 'charlie.davis@example.com', 'Germany', 'Berlin');
INSERT INTO customers VALUES (6, 'Diana', 'Miller', 'diana.miller@example.com', 'France', 'Paris');
INSERT INTO customers VALUES (7, 'Edward', 'Johnson', 'edward.johnson@example.com', 'Brazil', 'São Paulo');
INSERT INTO customers VALUES (8, 'Fiona', 'Garcia', 'fiona.garcia@example.com', 'Japan', 'Tokyo');
INSERT INTO customers VALUES (9, 'George', 'Martinez', 'george.martinez@example.com', 'Spain', 'Madrid');
INSERT INTO customers VALUES (10, 'Hannah', 'Anderson', 'hannah.anderson@example.com', 'Italy', 'Rome');

-- Insert Invoices
INSERT INTO invoices VALUES (1, 1, '2024-01-15', 9.99, '123 Main St', 'New York', 'USA');
INSERT INTO invoices VALUES (2, 2, '2024-01-20', 19.98, '456 Oak Ave', 'Toronto', 'Canada');
INSERT INTO invoices VALUES (3, 1, '2024-02-01', 14.97, '123 Main St', 'New York', 'USA');
INSERT INTO invoices VALUES (4, 3, '2024-02-10', 29.97, '789 Pine Rd', 'London', 'UK');
INSERT INTO invoices VALUES (5, 4, '2024-02-15', 9.99, '321 Beach Blvd', 'Sydney', 'Australia');
INSERT INTO invoices VALUES (6, 5, '2024-02-18', 9.99, '654 Elm St', 'Berlin', 'Germany');
INSERT INTO invoices VALUES (7, 6, '2024-02-20', 9.99, '987 Maple Dr', 'Paris', 'France');
INSERT INTO invoices VALUES (8, 7, '2024-02-22', 19.98, '147 Ocean Way', 'São Paulo', 'Brazil');
INSERT INTO invoices VALUES (9, 8, '2024-02-25', 9.99, '258 Mountain Ave', 'Tokyo', 'Japan');
INSERT INTO invoices VALUES (10, 9, '2024-02-28', 9.99, '369 Valley Rd', 'Madrid', 'Spain');

-- Insert Invoice Items
INSERT INTO invoice_items VALUES (1, 1, 1, 1, 0.99);
INSERT INTO invoice_items VALUES (2, 2, 3, 2, 0.99);
INSERT INTO invoice_items VALUES (3, 3, 5, 1, 0.99);
INSERT INTO invoice_items VALUES (4, 3, 6, 1, 0.99);
INSERT INTO invoice_items VALUES (5, 4, 9, 1, 0.99);
INSERT INTO invoice_items VALUES (6, 4, 10, 1, 0.99);
INSERT INTO invoice_items VALUES (7, 5, 13, 1, 0.99);
INSERT INTO invoice_items VALUES (8, 6, 17, 1, 0.99);
INSERT INTO invoice_items VALUES (9, 7, 21, 1, 0.99);
INSERT INTO invoice_items VALUES (10, 8, 1, 1, 0.99);