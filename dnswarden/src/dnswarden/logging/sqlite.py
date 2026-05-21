"""SQLite-based query logger."""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class SQLiteLogger:
    """Log DNS queries to SQLite database.

    Schema:
    CREATE TABLE dns_queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        client_ip TEXT,
        client_port INTEGER,
        query_name TEXT NOT NULL,
        query_type TEXT,
        response_code INTEGER,
        response_size INTEGER,
        protocol TEXT,
        latency_ms REAL,
        blocked BOOLEAN DEFAULT 0
    );
    """

    def __init__(self, db_path="/var/lib/dnswarden/logs.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._init_db()

    def _init_db(self):
        """Initialize database."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS dns_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                client_ip TEXT,
                client_port INTEGER,
                query_name TEXT NOT NULL,
                query_type TEXT,
                response_code INTEGER,
                response_size INTEGER,
                protocol TEXT,
                latency_ms REAL,
                blocked BOOLEAN DEFAULT 0,
                UNIQUE(timestamp, client_ip, query_name)
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_query_name ON dns_queries(query_name)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON dns_queries(timestamp)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_client_ip ON dns_queries(client_ip)")
        self.conn.commit()

    def log(self, request, response, client_addr, protocol, latency_ms):
        """Log a DNS query."""
        qname = str(request.q.qname).rstrip(".")
        qtype = str(request.q.qtype)
        rcode = response.header.rcode
        blocked = 1 if rcode == 3 else 0

        try:
            self.conn.execute(
                """
                INSERT OR IGNORE INTO dns_queries
                (timestamp, client_ip, client_port, query_name, query_type,
                 response_code, response_size, protocol, latency_ms, blocked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    datetime.utcnow().isoformat() + "Z",
                    client_addr[0],
                    client_addr[1],
                    qname,
                    qtype,
                    rcode,
                    len(response.pack()),
                    protocol,
                    latency_ms,
                    blocked,
                ),
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to log query: {e}")

    def query(self, filters=None, limit=100):
        """Query logs with filters."""
        sql = "SELECT * FROM dns_queries WHERE 1=1"
        params = []

        if filters:
            if "query_name" in filters:
                sql += " AND query_name LIKE ?"
                params.append(f"%{filters['query_name']}%")
            if "client_ip" in filters:
                sql += " AND client_ip = ?"
                params.append(filters["client_ip"])
            if "blocked" in filters:
                sql += " AND blocked = ?"
                params.append(filters["blocked"])

        sql += f" ORDER BY timestamp DESC LIMIT {limit}"

        cursor = self.conn.execute(sql, params)
        return cursor.fetchall()

    def get_stats(self):
        """Get blocking statistics."""
        cursor = self.conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(blocked) as blocked,
                COUNT(DISTINCT client_ip) as unique_clients
            FROM dns_queries
        """)
        return cursor.fetchone()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
