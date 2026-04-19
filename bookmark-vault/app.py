#!/usr/bin/env python3
"""
Bookmark Vault - A self-hosted bookmark manager
Run with: python app.py
"""

import os
import sqlite3
import json
import re
import csv
import io
from datetime import datetime
from functools import wraps
from html import escape
from urllib.parse import urlparse

from flask import Flask, request, jsonify, Response, send_file

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bookmarks.db')


# ==================== Database Setup ====================

def get_db():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize database with tables and FTS."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create bookmarks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            favicon TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_archived INTEGER DEFAULT 0
        )
    ''')
    
    # Create tags table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            color TEXT DEFAULT '#3B82F6',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create bookmark_tags join table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookmark_tags (
            bookmark_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (bookmark_id, tag_id),
            FOREIGN KEY (bookmark_id) REFERENCES bookmarks(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
    ''')
    
    # Create FTS5 virtual table for full-text search
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS bookmarks_fts USING fts5(
            title,
            description,
            url,
            content='bookmarks',
            content_rowid='id'
        )
    ''')
    
    # Create triggers to keep FTS in sync
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS bookmarks_ai AFTER INSERT ON bookmarks BEGIN
            INSERT INTO bookmarks_fts(rowid, title, description, url)
            VALUES (new.id, new.title, new.description, new.url);
        END
    ''')
    
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS bookmarks_ad AFTER DELETE ON bookmarks BEGIN
            INSERT INTO bookmarks_fts(bookmarks_fts, rowid, title, description, url)
            VALUES('delete', old.id, old.title, old.description, old.url);
        END
    ''')
    
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS bookmarks_au AFTER UPDATE ON bookmarks BEGIN
            INSERT INTO bookmarks_fts(bookmarks_fts, rowid, title, description, url)
            VALUES('delete', old.id, old.title, old.description, old.url);
            INSERT INTO bookmarks_fts(rowid, title, description, url)
            VALUES (new.id, new.title, new.description, new.url);
        END
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_bookmarks_url ON bookmarks(url)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_bookmarks_created ON bookmarks(created_at DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_bookmarks_archived ON bookmarks(is_archived)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)')
    
    conn.commit()
    conn.close()


# ==================== Helper Functions ====================

def row_to_dict(row):
    """Convert sqlite3.Row to dictionary."""
    if row is None:
        return None
    return dict(row)


def get_bookmark_tags(conn, bookmark_id):
    """Get all tags for a bookmark."""
    cursor = conn.execute('''
        SELECT t.* FROM tags t
        JOIN bookmark_tags bt ON t.id = bt.tag_id
        WHERE bt.bookmark_id = ?
    ''', (bookmark_id,))
    return [row_to_dict(row) for row in cursor.fetchall()]


def get_all_tags():
    """Get all tags with bookmark counts."""
    conn = get_db()
    cursor = conn.execute('''
        SELECT t.*, COUNT(bt.bookmark_id) as count
        FROM tags t
        LEFT JOIN bookmark_tags bt ON t.id = bt.tag_id
        GROUP BY t.id
        ORDER BY t.name
    ''')
    tags = [row_to_dict(row) for row in cursor.fetchall()]
    conn.close()
    return tags


def get_or_create_tag(conn, tag_name):
    """Get existing tag or create new one."""
    tag_name = tag_name.lower().strip()
    if not tag_name:
        return None
    
    # Try to get existing tag
    cursor = conn.execute('SELECT * FROM tags WHERE name = ?', (tag_name,))
    row = cursor.fetchone()
    if row:
        return row_to_dict(row)
    
    # Create new tag
    cursor = conn.execute(
        'INSERT INTO tags (name) VALUES (?)',
        (tag_name,)
    )
    conn.commit()
    return {'id': cursor.lastrowid, 'name': tag_name, 'color': '#3B82F6'}


def set_bookmark_tags(conn, bookmark_id, tag_names):
    """Set tags for a bookmark (replace all)."""
    # Remove existing tags
    conn.execute('DELETE FROM bookmark_tags WHERE bookmark_id = ?', (bookmark_id,))
    
    # Add new tags
    for tag_name in tag_names:
        if tag_name.strip():
            tag = get_or_create_tag(conn, tag_name.strip())
            if tag:
                try:
                    conn.execute(
                        'INSERT INTO bookmark_tags (bookmark_id, tag_id) VALUES (?, ?)',
                        (bookmark_id, tag['id'])
                    )
                except sqlite3.IntegrityError:
                    pass  # Already exists
    conn.commit()


def validate_url(url):
    """Validate and normalize URL."""
    if not url:
        return None
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    try:
        result = urlparse(url)
        if result.netloc:
            return url
    except:
        pass
    return None


# ==================== API Routes ====================

@app.route('/api/bookmarks', methods=['GET'])
def list_bookmarks():
    """List all bookmarks with optional filtering."""
    conn = get_db()
    
    tag = request.args.get('tag')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    archived = request.args.get('archived', 'false').lower() == 'true'
    
    offset = (page - 1) * limit
    
    # Build query
    if tag:
        query = '''
            SELECT DISTINCT b.* FROM bookmarks b
            JOIN bookmark_tags bt ON b.id = bt.bookmark_id
            JOIN tags t ON bt.tag_id = t.id
            WHERE t.name = ? AND b.is_archived = ?
            ORDER BY b.created_at DESC
            LIMIT ? OFFSET ?
        '''
        params = (tag.lower(), 1 if archived else 0, limit, offset)
    else:
        query = '''
            SELECT * FROM bookmarks
            WHERE is_archived = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        '''
        params = (1 if archived else 0, limit, offset)
    
    cursor = conn.execute(query, params)
    bookmarks = [row_to_dict(row) for row in cursor.fetchall()]
    
    # Get total count
    if tag:
        count_query = '''
            SELECT COUNT(DISTINCT b.id) FROM bookmarks b
            JOIN bookmark_tags bt ON b.id = bt.bookmark_id
            JOIN tags t ON bt.tag_id = t.id
            WHERE t.name = ? AND b.is_archived = ?
        '''
        total = conn.execute(count_query, (tag.lower(), 1 if archived else 0)).fetchone()[0]
    else:
        total = conn.execute(
            'SELECT COUNT(*) FROM bookmarks WHERE is_archived = ?',
            (1 if archived else 0,)
        ).fetchone()[0]
    
    # Add tags to each bookmark
    for bm in bookmarks:
        bm['tags'] = get_bookmark_tags(conn, bm['id'])
    
    conn.close()
    return jsonify({
        'results': bookmarks,
        'total': total,
        'page': page,
        'limit': limit
    })


@app.route('/api/bookmarks/<int:bookmark_id>', methods=['GET'])
def get_bookmark(bookmark_id):
    """Get a single bookmark."""
    conn = get_db()
    cursor = conn.execute('SELECT * FROM bookmarks WHERE id = ?', (bookmark_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({'error': 'Bookmark not found'}), 404
    
    bookmark = row_to_dict(row)
    bookmark['tags'] = get_bookmark_tags(conn, bookmark_id)
    conn.close()
    
    return jsonify(bookmark)


@app.route('/api/bookmarks', methods=['POST'])
def create_bookmark():
    """Create a new bookmark."""
    data = request.get_json()
    
    if not data or not data.get('url'):
        return jsonify({'error': 'URL is required'}), 400
    
    url = validate_url(data['url'])
    if not url:
        return jsonify({'error': 'Invalid URL'}), 400
    
    title = data.get('title', '').strip() or url
    description = data.get('description', '')
    tags = data.get('tags', [])
    
    conn = get_db()
    try:
        cursor = conn.execute(
            '''INSERT INTO bookmarks (url, title, description)
               VALUES (?, ?, ?)''',
            (url, title, description)
        )
        bookmark_id = cursor.lastrowid
        
        # Add tags
        if tags:
            set_bookmark_tags(conn, bookmark_id, tags)
        
        conn.commit()
        
        # Return created bookmark
        cursor = conn.execute('SELECT * FROM bookmarks WHERE id = ?', (bookmark_id,))
        bookmark = row_to_dict(cursor.fetchone())
        bookmark['tags'] = get_bookmark_tags(conn, bookmark_id)
        
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Bookmark with this URL already exists'}), 409
    
    conn.close()
    return jsonify(bookmark), 201


@app.route('/api/bookmarks/<int:bookmark_id>', methods=['PUT'])
def update_bookmark(bookmark_id):
    """Update a bookmark."""
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.execute('SELECT * FROM bookmarks WHERE id = ?', (bookmark_id,))
    
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Bookmark not found'}), 404
    
    # Build update query
    updates = []
    params = []
    
    if 'url' in data and data['url']:
        url = validate_url(data['url'])
        if url:
            updates.append('url = ?')
            params.append(url)
    
    if 'title' in data:
        updates.append('title = ?')
        params.append(data['title'])
    
    if 'description' in data:
        updates.append('description = ?')
        params.append(data['description'])
    
    if 'is_archived' in data:
        updates.append('is_archived = ?')
        params.append(1 if data['is_archived'] else 0)
    
    if updates:
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(bookmark_id)
        
        conn.execute(
            f"UPDATE bookmarks SET {', '.join(updates)} WHERE id = ?",
            params
        )
    
    # Update tags if provided
    if 'tags' in data:
        set_bookmark_tags(conn, bookmark_id, data['tags'])
    
    conn.commit()
    
    # Return updated bookmark
    cursor = conn.execute('SELECT * FROM bookmarks WHERE id = ?', (bookmark_id,))
    bookmark = row_to_dict(cursor.fetchone())
    bookmark['tags'] = get_bookmark_tags(conn, bookmark_id)
    
    conn.close()
    return jsonify(bookmark)


@app.route('/api/bookmarks/<int:bookmark_id>', methods=['DELETE'])
def delete_bookmark(bookmark_id):
    """Delete (archive) a bookmark."""
    conn = get_db()
    cursor = conn.execute('SELECT * FROM bookmarks WHERE id = ?', (bookmark_id,))
    
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Bookmark not found'}), 404
    
    # Soft delete (archive)
    conn.execute('UPDATE bookmarks SET is_archived = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (bookmark_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})


@app.route('/api/bookmarks/search', methods=['GET'])
def search_bookmarks():
    """Full-text search bookmarks."""
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    
    if not query:
        return jsonify({'results': [], 'total': 0, 'page': page})
    
    offset = (page - 1) * limit
    
    conn = get_db()
    
    # Escape special FTS characters and add wildcards
    fts_query = ' '.join(f'"{term}"*' for term in query.split() if term)
    
    try:
        # Search using FTS5
        cursor = conn.execute('''
            SELECT b.*, bm.rank
            FROM bookmarks b
            JOIN bookmarks_fts bm ON b.id = bm.rowid
            WHERE bookmarks_fts MATCH ? AND b.is_archived = 0
            ORDER BY bm.rank
            LIMIT ? OFFSET ?
        ''', (fts_query, limit, offset))
        
        bookmarks = [row_to_dict(row) for row in cursor.fetchall()]
        
        # Get total count
        total = conn.execute('''
            SELECT COUNT(*) FROM bookmarks b
            JOIN bookmarks_fts bm ON b.id = bm.rowid
            WHERE bookmarks_fts MATCH ? AND b.is_archived = 0
        ''', (fts_query,)).fetchone()[0]
        
    except sqlite3.OperationalError:
        # Fall back to LIKE search if FTS fails
        like_query = f'%{query}%'
        cursor = conn.execute('''
            SELECT * FROM bookmarks
            WHERE (title LIKE ? OR description LIKE ? OR url LIKE ?)
            AND is_archived = 0
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (like_query, like_query, like_query, limit, offset))
        
        bookmarks = [row_to_dict(row) for row in cursor.fetchall()]
        
        total = conn.execute('''
            SELECT COUNT(*) FROM bookmarks
            WHERE (title LIKE ? OR description LIKE ? OR url LIKE ?)
            AND is_archived = 0
        ''', (like_query, like_query, like_query)).fetchone()[0]
    
    # Add tags
    for bm in bookmarks:
        bm['tags'] = get_bookmark_tags(conn, bm['id'])
    
    conn.close()
    return jsonify({
        'results': bookmarks,
        'total': total,
        'page': page,
        'limit': limit
    })


# ==================== Tag Routes ====================

@app.route('/api/tags', methods=['GET'])
def list_tags():
    """List all tags with counts."""
    return jsonify(get_all_tags())


@app.route('/api/tags', methods=['POST'])
def create_tag():
    """Create a new tag."""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Tag name is required'}), 400
    
    name = data['name'].lower().strip()
    color = data.get('color', '#3B82F6')
    
    conn = get_db()
    try:
        cursor = conn.execute(
            'INSERT INTO tags (name, color) VALUES (?, ?)',
            (name, color)
        )
        tag_id = cursor.lastrowid
        conn.commit()
        
        tag = {'id': tag_id, 'name': name, 'color': color, 'count': 0}
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Tag already exists'}), 409
    
    conn.close()
    return jsonify(tag), 201


@app.route('/api/tags/<int:tag_id>', methods=['PUT'])
def update_tag(tag_id):
    """Update a tag."""
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.execute('SELECT * FROM tags WHERE id = ?', (tag_id,))
    
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Tag not found'}), 404
    
    updates = []
    params = []
    
    if 'name' in data:
        updates.append('name = ?')
        params.append(data['name'].lower().strip())
    
    if 'color' in data:
        updates.append('color = ?')
        params.append(data['color'])
    
    if updates:
        params.append(tag_id)
        conn.execute(f"UPDATE tags SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    
    cursor = conn.execute('SELECT * FROM tags WHERE id = ?', (tag_id,))
    tag = row_to_dict(cursor.fetchone())
    
    # Add count
    cursor = conn.execute(
        'SELECT COUNT(*) FROM bookmark_tags WHERE tag_id = ?',
        (tag_id,)
    )
    tag['count'] = cursor.fetchone()[0]
    
    conn.close()
    return jsonify(tag)


@app.route('/api/tags/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    """Delete a tag."""
    conn = get_db()
    cursor = conn.execute('SELECT * FROM tags WHERE id = ?', (tag_id,))
    
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Tag not found'}), 404
    
    conn.execute('DELETE FROM tags WHERE id = ?', (tag_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})


# ==================== Import/Export Routes ====================

@app.route('/api/import', methods=['POST'])
def import_bookmarks():
    """Import bookmarks from file."""
    format_type = request.args.get('format', 'json').lower()
    
    if 'file' in request.files:
        file = request.files['file']
        content = file.read().decode('utf-8')
    else:
        content = request.get_data(as_text=True)
    
    conn = get_db()
    imported = 0
    errors = []
    
    try:
        if format_type == 'json':
            imported, errors = import_json(conn, content)
        elif format_type == 'netscape':
            imported, errors = import_netscape(conn, content)
        elif format_type == 'csv':
            imported, errors = import_csv(conn, content)
        else:
            conn.close()
            return jsonify({'error': 'Unsupported format'}), 400
        
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400
    
    conn.close()
    return jsonify({
        'imported': imported,
        'errors': errors,
        'message': f'Successfully imported {imported} bookmarks'
    })


def import_json(conn, content):
    """Import bookmarks from JSON."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return 0, [f'Invalid JSON: {str(e)}']
    
    imported = 0
    errors = []
    
    if not isinstance(data, list):
        data = [data]
    
    for item in data:
        try:
            url = validate_url(item.get('url'))
            if not url:
                errors.append(f"Invalid URL: {item.get('url')}")
                continue
            
            title = item.get('title', '').strip() or url
            description = item.get('description', '')
            
            # Check if exists
            cursor = conn.execute('SELECT id FROM bookmarks WHERE url = ?', (url,))
            if cursor.fetchone():
                errors.append(f"Bookmark already exists: {url}")
                continue
            
            cursor = conn.execute(
                'INSERT INTO bookmarks (url, title, description) VALUES (?, ?, ?)',
                (url, title, description)
            )
            bookmark_id = cursor.lastrowid
            
            # Handle tags
            tags = item.get('tags', [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',') if t.strip()]
            
            if tags:
                set_bookmark_tags(conn, bookmark_id, tags)
            
            conn.commit()
            imported += 1
            
        except Exception as e:
            errors.append(f"Error importing {item.get('url')}: {str(e)}")
    
    return imported, errors


def import_netscape(conn, content):
    """Import bookmarks from Netscape HTML format."""
    import re
    
    # Parse Netscape HTML bookmark file
    # Match <A HREF="..." [ADD_DATE="..."] [TAGS="..."]>Title</A>
    pattern = re.compile(r'<A\s+HREF="([^"]+)"[^>]*>([^<]*)</A>', re.IGNORECASE)
    
    imported = 0
    errors = []
    
    # Find all links in the HTML
    for match in pattern.finditer(content):
        try:
            url = validate_url(match.group(1))
            if not url:
                errors.append(f"Invalid URL: {match.group(1)}")
                continue
            
            title = match.group(2).strip() or url
            
            # Check if exists
            cursor = conn.execute('SELECT id FROM bookmarks WHERE url = ?', (url,))
            if cursor.fetchone():
                continue  # Skip duplicates
            
            cursor = conn.execute(
                'INSERT INTO bookmarks (url, title) VALUES (?, ?)',
                (url, title)
            )
            bookmark_id = cursor.lastrowid
            conn.commit()
            imported += 1
            
        except Exception as e:
            errors.append(f"Error importing {match.group(1)}: {str(e)}")
    
    return imported, errors


def import_csv(conn, content):
    """Import bookmarks from CSV."""
    imported = 0
    errors = []
    
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        try:
            url = validate_url(row.get('url', ''))
            if not url:
                errors.append(f"Invalid URL: {row.get('url')}")
                continue
            
            title = row.get('title', '').strip() or url
            description = row.get('description', '')
            
            # Check if exists
            cursor = conn.execute('SELECT id FROM bookmarks WHERE url = ?', (url,))
            if cursor.fetchone():
                continue
            
            cursor = conn.execute(
                'INSERT INTO bookmarks (url, title, description) VALUES (?, ?, ?)',
                (url, title, description)
            )
            bookmark_id = cursor.lastrowid
            
            # Handle tags
            tags_str = row.get('tags', '')
            if tags_str:
                tags = [t.strip() for t in tags_str.split(',') if t.strip()]
                set_bookmark_tags(conn, bookmark_id, tags)
            
            conn.commit()
            imported += 1
            
        except Exception as e:
            errors.append(f"Error: {str(e)}")
    
    return imported, errors


@app.route('/api/export', methods=['GET'])
def export_bookmarks():
    """Export bookmarks to file."""
    format_type = request.args.get('format', 'json').lower()
    
    conn = get_db()
    cursor = conn.execute('SELECT * FROM bookmarks WHERE is_archived = 0 ORDER BY created_at DESC')
    bookmarks = [row_to_dict(row) for row in cursor.fetchall()]
    
    for bm in bookmarks:
        bm['tags'] = get_bookmark_tags(conn, bm['id'])
    
    conn.close()
    
    if format_type == 'json':
        return export_json(bookmarks)
    elif format_type == 'netscape':
        return export_netscape(bookmarks)
    elif format_type == 'csv':
        return export_csv(bookmarks)
    else:
        return jsonify({'error': 'Unsupported format'}), 400


def export_json(bookmarks):
    """Export bookmarks to JSON."""
    # Remove internal fields
    for bm in bookmarks:
        bm.pop('is_archived', None)
        bm['tags'] = [t['name'] for t in bm.get('tags', [])]
    
    response = Response(
        json.dumps(bookmarks, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment; filename=bookmarks.json'}
    )
    return response


def export_netscape(bookmarks):
    """Export bookmarks to Netscape HTML format."""
    html = '''<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file. -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
'''
    
    for bm in bookmarks:
        tags = bm.get('tags', [])
        tag_str = ','.join(t['name'] for t in tags) if tags else ''
        add_date = int(datetime.fromisoformat(bm['created_at'].replace('Z', '+00:00')).timestamp()) if bm.get('created_at') else ''
        
        html += f'    <DT><A HREF="{escape(bm["url"])}" ADD_DATE="{add_date}"'
        if tag_str:
            html += f' TAGS="{tag_str}"'
        html += f'>{escape(bm["title"])}</A>\n'
        
        if bm.get('description'):
            html += f'    <DD>{escape(bm["description"])}\n'
    
    html += '</DL><p>\n'
    
    response = Response(
        html,
        mimetype='text/html',
        headers={'Content-Disposition': 'attachment; filename=bookmarks.html'}
    )
    return response


def export_csv(bookmarks):
    """Export bookmarks to CSV."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['url', 'title', 'description', 'tags'])
    writer.writeheader()
    
    for bm in bookmarks:
        writer.writerow({
            'url': bm['url'],
            'title': bm['title'],
            'description': bm.get('description', ''),
            'tags': ','.join(t['name'] for t in bm.get('tags', []))
        })
    
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=bookmarks.csv'}
    )
    return response


# ==================== Static Files ====================

@app.route('/')
def index():
    """Serve main application."""
    return HTML_TEMPLATE


# ==================== HTML Template ====================

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bookmark Vault</title>
    <style>
        :root {
            --primary: #3B82F6;
            --primary-hover: #2563EB;
            --secondary: #64748B;
            --accent: #10B981;
            --bg: #F8FAFC;
            --surface: #FFFFFF;
            --text: #1E293B;
            --text-secondary: #64748B;
            --border: #E2E8F0;
            --danger: #EF4444;
            --shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        @media (prefers-color-scheme: dark) {
            :root {
                --bg: #0F172A;
                --surface: #1E293B;
                --text: #F1F5F9;
                --text-secondary: #94A3B8;
                --border: #334155;
            }
        }
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.5;
        }
        
        .app {
            display: flex;
            min-height: 100vh;
        }
        
        /* Sidebar */
        .sidebar {
            width: 260px;
            background: var(--surface);
            border-right: 1px solid var(--border);
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
        }
        
        .logo {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .sidebar-section {
            margin-bottom: 1.5rem;
        }
        
        .sidebar-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            color: var(--text-secondary);
            font-weight: 600;
            margin-bottom: 0.75rem;
        }
        
        .tag-list {
            list-style: none;
        }
        
        .tag-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.5rem 0.75rem;
            border-radius: 0.375rem;
            cursor: pointer;
            transition: background 0.15s;
        }
        
        .tag-item:hover, .tag-item.active {
            background: var(--border);
        }
        
        .tag-name {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .tag-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }
        
        .tag-count {
            font-size: 0.75rem;
            color: var(--text-secondary);
        }
        
        /* Main Content */
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        /* Header */
        .header {
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            padding: 1rem 1.5rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .search-box {
            flex: 1;
            max-width: 500px;
            position: relative;
        }
        
        .search-input {
            width: 100%;
            padding: 0.625rem 1rem 0.625rem 2.5rem;
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            background: var(--bg);
            color: var(--text);
            font-size: 0.875rem;
        }
        
        .search-input:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        .search-icon {
            position: absolute;
            left: 0.75rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
        }
        
        .header-actions {
            display: flex;
            gap: 0.5rem;
        }
        
        /* Buttons */
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 0.5rem;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s;
        }
        
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        
        .btn-primary:hover {
            background: var(--primary-hover);
        }
        
        .btn-secondary {
            background: var(--border);
            color: var(--text);
        }
        
        .btn-secondary:hover {
            background: var(--secondary);
            color: white;
        }
        
        .btn-icon {
            padding: 0.5rem;
        }
        
        .btn-danger {
            background: var(--danger);
            color: white;
        }
        
        /* Content Area */
        .content {
            flex: 1;
            padding: 1.5rem;
            overflow-y: auto;
        }
        
        /* Bookmark Grid */
        .bookmarks-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
        }
        
        .bookmark-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            padding: 1rem;
            transition: all 0.15s;
        }
        
        .bookmark-card:hover {
            border-color: var(--primary);
            box-shadow: var(--shadow);
        }
        
        .bookmark-header {
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            margin-bottom: 0.5rem;
        }
        
        .bookmark-favicon {
            width: 32px;
            height: 32px;
            border-radius: 0.375rem;
            background: var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
            flex-shrink: 0;
        }
        
        .bookmark-info {
            flex: 1;
            min-width: 0;
        }
        
        .bookmark-title {
            font-weight: 600;
            font-size: 0.9375rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .bookmark-url {
            font-size: 0.75rem;
            color: var(--text-secondary);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .bookmark-description {
            font-size: 0.8125rem;
            color: var(--text-secondary);
            margin: 0.5rem 0;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .bookmark-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.375rem;
            margin-top: 0.75rem;
        }
        
        .tag {
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            padding: 0.125rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.6875rem;
            font-weight: 500;
            background: var(--border);
            color: var(--text-secondary);
        }
        
        .tag .tag-dot {
            width: 6px;
            height: 6px;
        }
        
        .bookmark-actions {
            display: flex;
            gap: 0.25rem;
            margin-top: 0.75rem;
            padding-top: 0.75rem;
            border-top: 1px solid var(--border);
        }
        
        .empty-state {
            text-align: center;
            padding: 3rem;
            color: var(--text-secondary);
        }
        
        .empty-state svg {
            width: 64px;
            height: 64px;
            margin-bottom: 1rem;
            opacity: 0.5;
        }
        
        /* Modal */
        .modal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 100;
            opacity: 0;
            visibility: hidden;
            transition: all 0.2s;
        }
        
        .modal-overlay.active {
            opacity: 1;
            visibility: visible;
        }
        
        .modal {
            background: var(--surface);
            border-radius: 0.75rem;
            width: 100%;
            max-width: 500px;
            max-height: 90vh;
            overflow-y: auto;
            transform: scale(0.95);
            transition: transform 0.2s;
        }
        
        .modal-overlay.active .modal {
            transform: scale(1);
        }
        
        .modal-header {
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .modal-title {
            font-weight: 600;
            font-size: 1.125rem;
        }
        
        .modal-body {
            padding: 1.5rem;
        }
        
        .modal-footer {
            padding: 1rem 1.5rem;
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: flex-end;
            gap: 0.5rem;
        }
        
        /* Form */
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-label {
            display: block;
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 0.375rem;
        }
        
        .form-input, .form-textarea {
            width: 100%;
            padding: 0.625rem 0.75rem;
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            background: var(--bg);
            color: var(--text);
            font-size: 0.875rem;
        }
        
        .form-input:focus, .form-textarea:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        .form-textarea {
            min-height: 80px;
            resize: vertical;
        }
        
        /* Toast */
        .toast-container {
            position: fixed;
            bottom: 1.5rem;
            right: 1.5rem;
            z-index: 200;
        }
        
        .toast {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            padding: 0.75rem 1rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            margin-top: 0.5rem;
            animation: slideIn 0.2s ease;
        }
        
        .toast.success {
            border-left: 3px solid var(--accent);
        }
        
        .toast.error {
            border-left: 3px solid var(--danger);
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .sidebar {
                display: none;
            }
            
            .header {
                flex-wrap: wrap;
            }
            
            .search-box {
                order: 1;
                max-width: none;
                width: 100%;
                margin-top: 0.5rem;
            }
            
            .bookmarks-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* Import/Export Dropdown */
        .dropdown {
            position: relative;
        }
        
        .dropdown-menu {
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 0.25rem;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            min-width: 150px;
            z-index: 50;
            display: none;
        }
        
        .dropdown-menu.active {
            display: block;
        }
        
        .dropdown-item {
            display: block;
            width: 100%;
            padding: 0.5rem 1rem;
            text-align: left;
            background: none;
            border: none;
            color: var(--text);
            font-size: 0.875rem;
            cursor: pointer;
        }
        
        .dropdown-item:hover {
            background: var(--border);
        }
        
        .dropdown-divider {
            height: 1px;
            background: var(--border);
            margin: 0.25rem 0;
        }
    </style>
</head>
<body>
    <div class="app">
        <aside class="sidebar">
            <div class="logo">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z"/>
                </svg>
                Bookmark Vault
            </div>
            
            <div class="sidebar-section">
                <div class="sidebar-title">Tags</div>
                <ul class="tag-list" id="tagList">
                    <li class="tag-item active" data-tag="">
                        <span class="tag-name">All Bookmarks</span>
                    </li>
                </ul>
            </div>
        </aside>
        
        <main class="main">
            <header class="header">
                <div class="search-box">
                    <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                    </svg>
                    <input type="text" class="search-input" id="searchInput" placeholder="Search bookmarks...">
                </div>
                
                <div class="header-actions">
                    <div class="dropdown">
                        <button class="btn btn-secondary" onclick="toggleDropdown()">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                <polyline points="7,10 12,15 17,10"/><line x1="12" y1="15" x2="12" y2="3"/>
                            </svg>
                            Export
                        </button>
                        <div class="dropdown-menu" id="exportDropdown">
                            <button class="dropdown-item" onclick="exportBookmarks('json')">JSON</button>
                            <button class="dropdown-item" onclick="exportBookmarks('netscape')">Netscape HTML</button>
                            <button class="dropdown-item" onclick="exportBookmarks('csv')">CSV</button>
                        </div>
                    </div>
                    
                    <div class="dropdown">
                        <button class="btn btn-secondary" onclick="toggleImport()">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                <polyline points="17,8 12,3 7,8"/><line x1="12" y1="3" x2="12" y2="15"/>
                            </svg>
                            Import
                        </button>
                        <div class="dropdown-menu" id="importDropdown">
                            <button class="dropdown-item" onclick="showImportModal('json')">JSON</button>
                            <button class="dropdown-item" onclick="showImportModal('netscape')">Netscape HTML</button>
                            <button class="dropdown-item" onclick="showImportModal('csv')">CSV</button>
                        </div>
                    </div>
                    
                    <button class="btn btn-primary" onclick="showAddModal()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                        </svg>
                        Add Bookmark
                    </button>
                </div>
            </header>
            
            <div class="content">
                <div class="bookmarks-grid" id="bookmarksGrid">
                    <div class="empty-state">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z"/>
                        </svg>
                        <p>No bookmarks yet. Add your first bookmark!</p>
                    </div>
                </div>
            </div>
        </main>
    </div>
    
    <!-- Add/Edit Modal -->
    <div class="modal-overlay" id="bookmarkModal">
        <div class="modal">
            <div class="modal-header">
                <h2 class="modal-title" id="modalTitle">Add Bookmark</h2>
                <button class="btn btn-icon" onclick="closeModal()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            </div>
            <div class="modal-body">
                <form id="bookmarkForm">
                    <input type="hidden" id="bookmarkId">
                    <div class="form-group">
                        <label class="form-label">URL *</label>
                        <input type="url" class="form-input" id="bookmarkUrl" required placeholder="https://example.com">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Title</label>
                        <input type="text" class="form-input" id="bookmarkTitle" placeholder="Page title">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Description</label>
                        <textarea class="form-textarea" id="bookmarkDescription" placeholder="Optional notes..."></textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Tags (comma-separated)</label>
                        <input type="text" class="form-input" id="bookmarkTags" placeholder="work, tech, reading">
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button class="btn btn-primary" onclick="saveBookmark()">Save</button>
            </div>
        </div>
    </div>
    
    <!-- Import Modal -->
    <div class="modal-overlay" id="importModal">
        <div class="modal">
            <div class="modal-header">
                <h2 class="modal-title">Import Bookmarks</h2>
                <button class="btn btn-icon" onclick="closeImportModal()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            </div>
            <div class="modal-body">
                <form id="importForm">
                    <input type="hidden" id="importFormat">
                    <div class="form-group">
                        <label class="form-label">Select File</label>
                        <input type="file" class="form-input" id="importFile" accept=".json,.html,.csv">
                    </div>
                    <p style="font-size: 0.8125rem; color: var(--text-secondary);">
                        Or paste content directly:
                    </p>
                    <textarea class="form-textarea" id="importContent" placeholder="Paste JSON, HTML, or CSV content here..."></textarea>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeImportModal()">Cancel</button>
                <button class="btn btn-primary" onclick="doImport()">Import</button>
            </div>
        </div>
    </div>
    
    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer"></div>
    
    <script>
        let currentTag = '';
        let searchTimeout = null;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            loadTags();
            loadBookmarks();
            
            // Search
            document.getElementById('searchInput').addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => searchBookmarks(e.target.value), 300);
            });
            
            // Close dropdowns on outside click
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.dropdown')) {
                    document.querySelectorAll('.dropdown-menu').forEach(d => d.classList.remove('active'));
                }
            });
        });
        
        function toggleDropdown() {
            const dropdown = document.getElementById('exportDropdown');
            dropdown.classList.toggle('active');
            document.getElementById('importDropdown').classList.remove('active');
        }
        
        function toggleImport() {
            const dropdown = document.getElementById('importDropdown');
            dropdown.classList.toggle('active');
            document.getElementById('exportDropdown').classList.remove('active');
        }
        
        // Tags
        async function loadTags() {
            try {
                const res = await fetch('/api/tags');
                const tags = await res.json();
                
                const tagList = document.getElementById('tagList');
                tagList.innerHTML = `
                    <li class="tag-item ${!currentTag ? 'active' : ''}" data-tag="" onclick="filterByTag('')">
                        <span class="tag-name">All Bookmarks</span>
                    </li>
                `;
                
                tags.forEach(tag => {
                    const li = document.createElement('li');
                    li.className = `tag-item ${currentTag === tag.name ? 'active' : ''}`;
                    li.dataset.tag = tag.name;
                    li.onclick = () => filterByTag(tag.name);
                    li.innerHTML = `
                        <span class="tag-name">
                            <span class="tag-dot" style="background: ${tag.color}"></span>
                            ${tag.name}
                        </span>
                        <span class="tag-count">${tag.count}</span>
                    `;
                    tagList.appendChild(li);
                });
            } catch (e) {
                console.error('Failed to load tags:', e);
            }
        }
        
        function filterByTag(tag) {
            currentTag = tag;
            document.querySelectorAll('.tag-item').forEach(item => {
                item.classList.toggle('active', item.dataset.tag === tag);
            });
            loadBookmarks();
        }
        
        // Bookmarks
        async function loadBookmarks() {
            const grid = document.getElementById('bookmarksGrid');
            grid.innerHTML = '<div class="empty-state"><p>Loading...</p></div>';
            
            try {
                let url = '/api/bookmarks?limit=100';
                if (currentTag) {
                    url += '&tag=' + encodeURIComponent(currentTag);
                }
                
                const res = await fetch(url);
                const data = await res.json();
                
                if (data.results.length === 0) {
                    grid.innerHTML = `
                        <div class="empty-state">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <path d="M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z"/>
                            </svg>
                            <p>No bookmarks ${currentTag ? 'with tag "' + currentTag + '"' : 'yet'}. Add your first!</p>
                        </div>
                    `;
                    return;
                }
                
                grid.innerHTML = data.results.map(bm => `
                    <div class="bookmark-card">
                        <div class="bookmark-header">
                            <div class="bookmark-favicon">${getFaviconEmoji(bm.url)}</div>
                            <div class="bookmark-info">
                                <div class="bookmark-title">${escapeHtml(bm.title)}</div>
                                <div class="bookmark-url">${escapeHtml(bm.url)}</div>
                            </div>
                        </div>
                        ${bm.description ? `<div class="bookmark-description">${escapeHtml(bm.description)}</div>` : ''}
                        ${bm.tags && bm.tags.length ? `
                            <div class="bookmark-tags">
                                ${bm.tags.map(tag => `
                                    <span class="tag">
                                        <span class="tag-dot" style="background: ${tag.color}"></span>
                                        ${escapeHtml(tag.name)}
                                    </span>
                                `).join('')}
                            </div>
                        ` : ''}
                        <div class="bookmark-actions">
                            <button class="btn btn-secondary btn-icon" onclick="openBookmark('${escapeHtml(bm.url)}')" title="Open">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                                    <polyline points="15,3 21,3 21,9"/><line x1="10" y1="14" x2="21" y2="3"/>
                                </svg>
                            </button>
                            <button class="btn btn-secondary btn-icon" onclick="editBookmark(${bm.id})" title="Edit">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                                </svg>
                            </button>
                            <button class="btn btn-danger btn-icon" onclick="deleteBookmark(${bm.id})" title="Delete">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="3,6 5,6 21,6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                `).join('');
            } catch (e) {
                console.error('Failed to load bookmarks:', e);
                grid.innerHTML = '<div class="empty-state"><p>Failed to load bookmarks</p></div>';
            }
        }
        
        async function searchBookmarks(query) {
            if (!query) {
                loadBookmarks();
                return;
            }
            
            const grid = document.getElementById('bookmarksGrid');
            grid.innerHTML = '<div class="empty-state"><p>Searching...</p></div>';
            
            try {
                const res = await fetch('/api/bookmarks/search?q=' + encodeURIComponent(query));
                const data = await res.json();
                
                if (data.results.length === 0) {
                    grid.innerHTML = `
                        <div class="empty-state">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                            </svg>
                            <p>No results for "${escapeHtml(query)}"</p>
                        </div>
                    `;
                    return;
                }
                
                grid.innerHTML = data.results.map(bm => `
                    <div class="bookmark-card">
                        <div class="bookmark-header">
                            <div class="bookmark-favicon">${getFaviconEmoji(bm.url)}</div>
                            <div class="bookmark-info">
                                <div class="bookmark-title">${escapeHtml(bm.title)}</div>
                                <div class="bookmark-url">${escapeHtml(bm.url)}</div>
                            </div>
                        </div>
                        ${bm.description ? `<div class="bookmark-description">${escapeHtml(bm.description)}</div>` : ''}
                        ${bm.tags && bm.tags.length ? `
                            <div class="bookmark-tags">
                                ${bm.tags.map(tag => `
                                    <span class="tag">
                                        <span class="tag-dot" style="background: ${tag.color}"></span>
                                        ${escapeHtml(tag.name)}
                                    </span>
                                `).join('')}
                            </div>
                        ` : ''}
                        <div class="bookmark-actions">
                            <button class="btn btn-secondary btn-icon" onclick="openBookmark('${escapeHtml(bm.url)}')" title="Open">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                                    <polyline points="15,3 21,3 21,9"/><line x1="10" y1="14" x2="21" y2="3"/>
                                </svg>
                            </button>
                            <button class="btn btn-secondary btn-icon" onclick="editBookmark(${bm.id})" title="Edit">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                                </svg>
                            </button>
                            <button class="btn btn-danger btn-icon" onclick="deleteBookmark(${bm.id})" title="Delete">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="3,6 5,6 21,6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                `).join('');
            } catch (e) {
                console.error('Search failed:', e);
                grid.innerHTML = '<div class="empty-state"><p>Search failed</p></div>';
            }
        }
        
        // Modal functions
        function showAddModal() {
            document.getElementById('modalTitle').textContent = 'Add Bookmark';
            document.getElementById('bookmarkId').value = '';
            document.getElementById('bookmarkForm').reset();
            document.getElementById('bookmarkModal').classList.add('active');
        }
        
        async function editBookmark(id) {
            try {
                const res = await fetch('/api/bookmarks/' + id);
                const bm = await res.json();
                
                document.getElementById('modalTitle').textContent = 'Edit Bookmark';
                document.getElementById('bookmarkId').value = bm.id;
                document.getElementById('bookmarkUrl').value = bm.url;
                document.getElementById('bookmarkTitle').value = bm.title || '';
                document.getElementById('bookmarkDescription').value = bm.description || '';
                document.getElementById('bookmarkTags').value = (bm.tags || []).map(t => t.name).join(', ');
                
                document.getElementById('bookmarkModal').classList.add('active');
            } catch (e) {
                showToast('Failed to load bookmark', 'error');
            }
        }
        
        function closeModal() {
            document.getElementById('bookmarkModal').classList.remove('active');
        }
        
        async function saveBookmark() {
            const id = document.getElementById('bookmarkId').value;
            const url = document.getElementById('bookmarkUrl').value.trim();
            const title = document.getElementById('bookmarkTitle').value.trim();
            const description = document.getElementById('bookmarkDescription').value.trim();
            const tagsStr = document.getElementById('bookmarkTags').value;
            
            if (!url) {
                showToast('URL is required', 'error');
                return;
            }
            
            const tags = tagsStr.split(',').map(t => t.trim()).filter(t => t);
            
            const data = { url, title: title || url, description, tags };
            
            try {
                let res;
                if (id) {
                    res = await fetch('/api/bookmarks/' + id, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                } else {
                    res = await fetch('/api/bookmarks', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                }
                
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.error || 'Failed to save');
                }
                
                closeModal();
                loadBookmarks();
                loadTags();
                showToast(id ? 'Bookmark updated' : 'Bookmark added', 'success');
            } catch (e) {
                showToast(e.message, 'error');
            }
        }
        
        async function deleteBookmark(id) {
            if (!confirm('Are you sure you want to delete this bookmark?')) return;
            
            try {
                const res = await fetch('/api/bookmarks/' + id, { method: 'DELETE' });
                if (!res.ok) throw new Error('Failed to delete');
                
                loadBookmarks();
                loadTags();
                showToast('Bookmark deleted', 'success');
            } catch (e) {
                showToast('Failed to delete bookmark', 'error');
            }
        }
        
        function openBookmark(url) {
            window.open(url, '_blank');
        }
        
        // Import/Export
        function showImportModal(format) {
            document.getElementById('importFormat').value = format;
            document.getElementById('importForm').reset();
            document.getElementById('importModal').classList.add('active');
            document.getElementById('importDropdown').classList.remove('active');
        }
        
        function closeImportModal() {
            document.getElementById('importModal').classList.remove('active');
        }
        
        async function doImport() {
            const format = document.getElementById('importFormat').value;
            const file = document.getElementById('importFile').files[0];
            const content = document.getElementById('importContent').value.trim();
            
            const formData = new FormData();
            if (file) {
                formData.append('file', file);
            } else if (content) {
                formData.append('content', content);
            } else {
                showToast('Please select a file or paste content', 'error');
                return;
            }
            
            try {
                const res = await fetch('/api/import?format=' + format, {
                    method: 'POST',
                    body: file ? formData : content
                });
                
                const data = await res.json();
                
                if (!res.ok) {
                    throw new Error(data.error || 'Import failed');
                }
                
                closeImportModal();
                loadBookmarks();
                loadTags();
                showToast(data.message, 'success');
            } catch (e) {
                showToast(e.message, 'error');
            }
        }
        
        function exportBookmarks(format) {
            document.getElementById('exportDropdown').classList.remove('active');
            window.location.href = '/api/export?format=' + format;
        }
        
        // Utilities
        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function getFaviconEmoji(url) {
            try {
                const domain = new URL(url).hostname;
                return domain.charAt(0).toUpperCase();
            } catch {
                return '?';
            }
        }
        
        function showToast(message, type = 'success') {
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = 'toast ' + type;
            toast.textContent = message;
            container.appendChild(toast);
            
            setTimeout(() => toast.remove(), 3000);
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    # Initialize database
    init_db()
    print("Bookmark Vault starting on http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
