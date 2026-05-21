import sqlite3
import os
from config import Config

def init_db():
    """Initialize the database with required tables."""
    os.makedirs(os.path.dirname(Config.DATABASE), exist_ok=True)
    
    conn = sqlite3.connect(Config.DATABASE)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            query TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            rows_affected INTEGER DEFAULT 0,
            execution_time REAL DEFAULT 0,
            error TEXT,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_dbs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            schema_json TEXT,
            data_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_history_executed_at 
        ON query_history(executed_at DESC)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_saved_queries_name 
        ON saved_queries(name)
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized at {Config.DATABASE}")

if __name__ == '__main__':
    init_db()
