from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime
from io import BytesIO
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize database on startup
from database.init_db import init_db
init_db()

def get_db():
    """Get database connection with row factory."""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# ==================== Routes ====================

@app.route('/')
def index():
    """Main playground page."""
    return render_template('index.html')

@app.route('/history')
def history():
    """Query history page."""
    return render_template('history.html')

# ==================== API Routes ====================

@app.route('/api/query/history', methods=['GET'])
def get_query_history():
    """Get query history with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Validate pagination params
    page = max(1, page)
    per_page = min(max(1, per_page), Config.MAX_PAGE_SIZE)
    offset = (page - 1) * per_page
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM query_history')
        total = cursor.fetchone()[0]
        
        # Get paginated history
        cursor.execute('''
            SELECT id, query, rows_affected, execution_time, error, executed_at
            FROM query_history
            ORDER BY executed_at DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'id': row['id'],
                'query': row['query'],
                'row_count': row['rows_affected'],
                'execution_time': row['execution_time'],
                'error': row['error'],
                'executed_at': row['executed_at']
            })
        
        return jsonify({
            'history': history,
            'total': total,
            'page': page,
            'per_page': per_page
        })
    finally:
        conn.close()

@app.route('/api/query/history', methods=['POST'])
def save_query_history():
    """Save a query to history."""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'success': False, 'error': 'Query is required'}), 400
        
        query = data.get('query', '').strip()
        if not query:
            return jsonify({'success': False, 'error': 'Query cannot be empty'}), 400
        
        # Truncate very long queries
        if len(query) > 10000:
            query = query[:10000]
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO query_history (query, rows_affected, execution_time, error, executed_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                query,
                data.get('row_count', 0),
                data.get('execution_time', 0),
                data.get('error'),
                datetime.utcnow().isoformat()
            ))
            
            conn.commit()
            history_id = cursor.lastrowid
            
            return jsonify({'success': True, 'id': history_id})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/query/history/<int:id>', methods=['DELETE'])
def delete_history_item(id):
    """Delete a history item."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM query_history WHERE id = ?', (id,))
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()

@app.route('/api/query/history', methods=['DELETE'])
def clear_history():
    """Clear all history."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM query_history')
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()

@app.route('/api/query/save', methods=['POST'])
def save_query():
    """Save a named query."""
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'query' not in data:
            return jsonify({'success': False, 'error': 'Name and query are required'}), 400
        
        name = data.get('name', '').strip()
        query = data.get('query', '').strip()
        
        if not name or not query:
            return jsonify({'success': False, 'error': 'Name and query cannot be empty'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO saved_queries (name, query, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (
                name,
                query,
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            ))
            
            conn.commit()
            query_id = cursor.lastrowid
            
            return jsonify({'success': True, 'id': query_id})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/query/saved', methods=['GET'])
def get_saved_queries():
    """Get all saved queries."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, name, query, created_at, updated_at
            FROM saved_queries
            ORDER BY updated_at DESC
        ''')
        
        queries = []
        for row in cursor.fetchall():
            queries.append({
                'id': row['id'],
                'name': row['name'],
                'query': row['query'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        return jsonify({'queries': queries})
    finally:
        conn.close()

@app.route('/api/query/saved/<int:id>', methods=['DELETE'])
def delete_saved_query(id):
    """Delete a saved query."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM saved_queries WHERE id = ?', (id,))
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()

@app.route('/api/db/samples', methods=['GET'])
def get_sample_datasets():
    """Get list of available sample datasets."""
    samples = [
        {
            'id': 'employees',
            'name': 'Employees',
            'description': 'Employee data with departments and salaries',
            'tables': ['employees', 'departments']
        },
        {
            'id': 'products',
            'name': 'Products',
            'description': 'E-commerce product catalog',
            'tables': ['products', 'categories']
        },
        {
            'id': 'orders',
            'name': 'Orders',
            'description': 'Customer orders and order items',
            'tables': ['orders', 'order_items', 'customers']
        },
        {
            'id': 'chinook',
            'name': 'Chinook',
            'description': 'Music store database with artists, albums, tracks',
            'tables': ['artists', 'albums', 'tracks', 'invoices', 'customers']
        }
    ]
    
    return jsonify({'samples': samples})

@app.route('/api/db/load-sample', methods=['POST'])
def load_sample():
    """Load a sample dataset - returns SQL to execute client-side."""
    try:
        data = request.get_json()
        
        if not data or 'dataset' not in data:
            return jsonify({'success': False, 'error': 'Dataset ID is required'}), 400
        
        sample_id = data.get('dataset')
        
        # SQL statements for sample datasets
        samples = {
            'employees': {
                'name': 'Employees',
                'sql': '''
                    CREATE TABLE IF NOT EXISTS employees (
                        id INTEGER PRIMARY KEY,
                        first_name TEXT,
                        last_name TEXT,
                        email TEXT,
                        department_id INTEGER,
                        salary INTEGER,
                        hire_date TEXT
                    );
                    INSERT INTO employees VALUES (1, 'John', 'Doe', 'john@example.com', 1, 50000, '2020-01-15');
                    INSERT INTO employees VALUES (2, 'Jane', 'Smith', 'jane@example.com', 2, 55000, '2019-03-22');
                    INSERT INTO employees VALUES (3, 'Bob', 'Johnson', 'bob@example.com', 1, 48000, '2021-06-10');
                    INSERT INTO employees VALUES (4, 'Alice', 'Williams', 'alice@example.com', 3, 62000, '2018-09-01');
                    INSERT INTO employees VALUES (5, 'Charlie', 'Brown', 'charlie@example.com', 2, 52000, '2020-11-15');
                    INSERT INTO employees VALUES (6, 'Diana', 'Miller', 'diana@example.com', 4, 58000, '2017-05-20');
                    INSERT INTO employees VALUES (7, 'Edward', 'Davis', 'edward@example.com', 1, 65000, '2019-08-10');
                    INSERT INTO employees VALUES (8, 'Fiona', 'Garcia', 'fiona@example.com', 3, 55000, '2021-02-28');
                    INSERT INTO employees VALUES (9, 'George', 'Martinez', 'george@example.com', 4, 49000, '2022-01-05');
                    INSERT INTO employees VALUES (10, 'Hannah', 'Wilson', 'hannah@example.com', 2, 51000, '2020-07-12');
                    
                    CREATE TABLE IF NOT EXISTS departments (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        budget INTEGER
                    );
                    INSERT INTO departments VALUES (1, 'Engineering', 500000);
                    INSERT INTO departments VALUES (2, 'Marketing', 200000);
                    INSERT INTO departments VALUES (3, 'Sales', 300000);
                    INSERT INTO departments VALUES (4, 'Human Resources', 150000);
                '''
            },
            'products': {
                'name': 'Products',
                'sql': '''
                    CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        price REAL,
                        category_id INTEGER,
                        stock INTEGER
                    );
                    INSERT INTO products VALUES (1, 'Laptop', 999.99, 1, 50);
                    INSERT INTO products VALUES (2, 'Mouse', 29.99, 2, 200);
                    INSERT INTO products VALUES (3, 'Keyboard', 79.99, 2, 150);
                    INSERT INTO products VALUES (4, 'Monitor', 299.99, 1, 75);
                    INSERT INTO products VALUES (5, 'Headphones', 149.99, 2, 120);
                    INSERT INTO products VALUES (6, 'Webcam', 89.99, 2, 90);
                    INSERT INTO products VALUES (7, 'USB Cable', 9.99, 2, 500);
                    INSERT INTO products VALUES (8, 'External SSD', 129.99, 1, 60);
                    INSERT INTO products VALUES (9, 'Graphics Card', 499.99, 1, 25);
                    INSERT INTO products VALUES (10, 'RAM 16GB', 79.99, 1, 100);
                    
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY,
                        name TEXT
                    );
                    INSERT INTO categories VALUES (1, 'Electronics');
                    INSERT INTO categories VALUES (2, 'Accessories');
                '''
            },
            'orders': {
                'name': 'Orders',
                'sql': '''
                    CREATE TABLE IF NOT EXISTS customers (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        email TEXT,
                        city TEXT
                    );
                    INSERT INTO customers VALUES (1, 'John Smith', 'john@example.com', 'New York');
                    INSERT INTO customers VALUES (2, 'Jane Doe', 'jane@example.com', 'Los Angeles');
                    INSERT INTO customers VALUES (3, 'Bob Wilson', 'bob@example.com', 'Chicago');
                    INSERT INTO customers VALUES (4, 'Alice Brown', 'alice@example.com', 'Houston');
                    INSERT INTO customers VALUES (5, 'Charlie Davis', 'charlie@example.com', 'Phoenix');
                    
                    CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY,
                        customer_id INTEGER,
                        order_date TEXT,
                        total REAL
                    );
                    INSERT INTO orders VALUES (1, 1, '2024-01-15', 129.98);
                    INSERT INTO orders VALUES (2, 2, '2024-01-16', 299.99);
                    INSERT INTO orders VALUES (3, 1, '2024-01-20', 89.99);
                    INSERT INTO orders VALUES (4, 3, '2024-02-01', 549.98);
                    INSERT INTO orders VALUES (5, 4, '2024-02-05', 179.98);
                    INSERT INTO orders VALUES (6, 5, '2024-02-10', 229.99);
                    
                    CREATE TABLE IF NOT EXISTS order_items (
                        id INTEGER PRIMARY KEY,
                        order_id INTEGER,
                        product_name TEXT,
                        quantity INTEGER,
                        price REAL
                    );
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
                '''
            },
            'chinook': {
                'name': 'Chinook',
                'sql': '''
                    CREATE TABLE IF NOT EXISTS artists (
                        artist_id INTEGER PRIMARY KEY,
                        name TEXT
                    );
                    INSERT INTO artists VALUES (1, 'AC/DC');
                    INSERT INTO artists VALUES (2, 'Led Zeppelin');
                    INSERT INTO artists VALUES (3, 'Metallica');
                    INSERT INTO artists VALUES (4, 'The Rolling Stones');
                    INSERT INTO artists VALUES (5, 'U2');
                    
                    CREATE TABLE IF NOT EXISTS albums (
                        album_id INTEGER PRIMARY KEY,
                        title TEXT,
                        artist_id INTEGER
                    );
                    INSERT INTO albums VALUES (1, 'For Those About to Rock', 1);
                    INSERT INTO albums VALUES (2, 'Physical Graffiti', 2);
                    INSERT INTO albums VALUES (3, 'Master of Puppets', 3);
                    INSERT INTO albums VALUES (4, 'Some Girls', 4);
                    INSERT INTO albums VALUES (5, 'The Joshua Tree', 5);
                    
                    CREATE TABLE IF NOT EXISTS tracks (
                        track_id INTEGER PRIMARY KEY,
                        name TEXT,
                        album_id INTEGER,
                        milliseconds INTEGER,
                        price REAL
                    );
                    INSERT INTO tracks VALUES (1, 'For Those About to Rock', 1, 343719, 0.99);
                    INSERT INTO tracks VALUES (2, 'Kashmir', 2, 523328, 0.99);
                    INSERT INTO tracks VALUES (3, 'Battery', 3, 302530, 0.99);
                    INSERT INTO tracks VALUES (4, 'Miss You', 4, 261049, 0.99);
                    INSERT INTO tracks VALUES (5, 'Where the Streets Have No Name', 5, 300552, 0.99);
                    INSERT INTO tracks VALUES (6, 'Stairway to Heaven', 2, 482444, 0.99);
                    INSERT INTO tracks VALUES (7, 'Enter Sandman', 3, 331180, 0.99);
                    INSERT INTO tracks VALUES (8, 'Sweet Child O Mine', 3, 356493, 0.99);
                    INSERT INTO tracks VALUES (9, 'Back in Black', 1, 255691, 0.99);
                    INSERT INTO tracks VALUES (10, 'Rock and Roll', 2, 240789, 0.99);
                    
                    CREATE TABLE IF NOT EXISTS customers (
                        customer_id INTEGER PRIMARY KEY,
                        first_name TEXT,
                        last_name TEXT,
                        email TEXT,
                        country TEXT
                    );
                    INSERT INTO customers VALUES (1, 'John', 'Smith', 'john.smith@example.com', 'USA');
                    INSERT INTO customers VALUES (2, 'Jane', 'Doe', 'jane.doe@example.com', 'Canada');
                    INSERT INTO customers VALUES (3, 'Bob', 'Johnson', 'bob.j@example.com', 'UK');
                    INSERT INTO customers VALUES (4, 'Alice', 'Williams', 'alice.w@example.com', 'Australia');
                    INSERT INTO customers VALUES (5, 'Charlie', 'Brown', 'charlie.b@example.com', 'Germany');
                    
                    CREATE TABLE IF NOT EXISTS invoices (
                        invoice_id INTEGER PRIMARY KEY,
                        customer_id INTEGER,
                        invoice_date TEXT,
                        total REAL
                    );
                    INSERT INTO invoices VALUES (1, 1, '2024-01-15', 9.99);
                    INSERT INTO invoices VALUES (2, 2, '2024-01-20', 19.98);
                    INSERT INTO invoices VALUES (3, 1, '2024-02-01', 14.97);
                    INSERT INTO invoices VALUES (4, 3, '2024-02-10', 29.97);
                    INSERT INTO invoices VALUES (5, 4, '2024-02-15', 9.99);
                '''
            }
        }
        
        sample = samples.get(sample_id)
        if not sample:
            return jsonify({'success': False, 'error': 'Sample not found'}), 404
        
        return jsonify({
            'success': True,
            'name': sample['name'],
            'sql': sample['sql']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export_data():
    """Export data to CSV or JSON format."""
    try:
        data = request.get_json()
        format_type = data.get('format', 'csv')
        columns = data.get('columns', [])
        rows = data.get('rows', [])
        
        if format_type == 'csv':
            # Build CSV content
            csv_content = ','.join(f'"{col}"' for col in columns) + '\n'
            for row in rows:
                csv_content += ','.join(f'"{cell}"' if cell is not None else '' for cell in row) + '\n'
            
            return send_file(
                BytesIO(csv_content.encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name='export.csv'
            )
        
        elif format_type == 'json':
            json_data = []
            for row in rows:
                obj = {}
                for i, col in enumerate(columns):
                    obj[col] = row[i] if i < len(row) else None
                json_data.append(obj)
            
            content = json.dumps(json_data, indent=2)
            
            return send_file(
                BytesIO(content.encode('utf-8')),
                mimetype='application/json',
                as_attachment=True,
                download_name='export.json'
            )
        
        return jsonify({'success': False, 'error': 'Invalid format'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
