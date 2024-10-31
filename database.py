import os
import json
from datetime import datetime, timedelta
from typing import Optional
import psycopg2
from psycopg2.extras import Json
from models import Dataset, SearchResult

class DatabaseManager:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.environ['PGDATABASE'],
            user=os.environ['PGUSER'],
            password=os.environ['PGPASSWORD'],
            host=os.environ['PGHOST'],
            port=os.environ['PGPORT']
        )
        self._create_tables()

    def _create_tables(self):
        with self.conn.cursor() as cur:
            # Drop the type if it exists
            cur.execute("DROP TYPE IF EXISTS search_cache CASCADE")
            
            # Create the table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    query TEXT PRIMARY KEY,
                    results JSONB,
                    timestamp TIMESTAMP
                )
            """)
        self.conn.commit()

    def get_cached_results(self, query: str) -> Optional[SearchResult]:
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT results, timestamp FROM search_cache WHERE query = %s",
                (query,)
            )
            result = cur.fetchone()
            
            if not result:
                return None
                
            results_json, timestamp = result
            
            # Check if cache is older than 24 hours
            if datetime.now() - timestamp > timedelta(hours=24):
                return None
                
            return SearchResult(**results_json)

    def cache_results(self, query: str, results: SearchResult):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO search_cache (query, results, timestamp)
                VALUES (%s, %s, %s)
                ON CONFLICT (query) DO UPDATE
                SET results = EXCLUDED.results,
                    timestamp = EXCLUDED.timestamp
                """,
                (query, Json(results.__dict__), datetime.now())
            )
        self.conn.commit()
