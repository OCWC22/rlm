"""
Neon PostgreSQL storage for JSON Explorer.

Uses Neon's serverless PostgreSQL for:
- Query result caching
- Session state persistence
- Execution trace storage

Design:
- Async-first using asyncpg
- Connection pooling for performance
- Automatic schema migrations
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any
from dataclasses import dataclass

# Neon/asyncpg imports
try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False
    asyncpg = None


@dataclass
class CacheEntry:
    """A cached query result."""
    key: str
    value: str
    created_at: datetime
    expires_at: Optional[datetime]
    metadata: dict


class NeonStorage:
    """
    Neon PostgreSQL storage backend.
    
    Environment variables:
        NEON_DATABASE_URL: PostgreSQL connection string
        
    Example:
        >>> storage = NeonStorage()
        >>> await storage.connect()
        >>> await storage.cache_set("key", "value", ttl=3600)
        >>> value = await storage.cache_get("key")
    """
    
    # SQL for schema setup
    SCHEMA_SQL = """
    -- Query cache table
    CREATE TABLE IF NOT EXISTS query_cache (
        cache_key TEXT PRIMARY KEY,
        cache_value TEXT NOT NULL,
        file_hash TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        expires_at TIMESTAMPTZ,
        metadata JSONB DEFAULT '{}'
    );
    
    -- Index for expiration cleanup
    CREATE INDEX IF NOT EXISTS idx_cache_expires 
    ON query_cache(expires_at) 
    WHERE expires_at IS NOT NULL;
    
    -- Session state table
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        file_path TEXT,
        schema_json JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        last_accessed TIMESTAMPTZ DEFAULT NOW(),
        metadata JSONB DEFAULT '{}'
    );
    
    -- Execution traces table
    CREATE TABLE IF NOT EXISTS execution_traces (
        trace_id TEXT PRIMARY KEY,
        session_id TEXT REFERENCES sessions(session_id) ON DELETE CASCADE,
        query TEXT NOT NULL,
        trace_json JSONB NOT NULL,
        tokens_used INTEGER DEFAULT 0,
        duration_ms REAL DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    
    -- Index for trace lookup
    CREATE INDEX IF NOT EXISTS idx_traces_session 
    ON execution_traces(session_id, created_at DESC);
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        pool_size: int = 5,
    ):
        """
        Initialize Neon storage.
        
        Args:
            database_url: Neon PostgreSQL URL (or use NEON_DATABASE_URL env)
            pool_size: Connection pool size
        """
        if not HAS_ASYNCPG:
            raise ImportError(
                "asyncpg not installed. Run: pip install asyncpg"
            )
        
        self.database_url = database_url or os.environ.get("NEON_DATABASE_URL")
        if not self.database_url:
            raise ValueError(
                "NEON_DATABASE_URL environment variable required"
            )
        
        self.pool_size = pool_size
        self._pool: Optional[asyncpg.Pool] = None
    
    async def connect(self) -> None:
        """Connect to Neon and initialize schema."""
        self._pool = await asyncpg.create_pool(
            self.database_url,
            min_size=1,
            max_size=self.pool_size,
            # Neon requires SSL
            ssl="require",
        )
        
        # Initialize schema
        async with self._pool.acquire() as conn:
            await conn.execute(self.SCHEMA_SQL)
    
    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
    
    # ─────────────────────────────────────────────────────────────
    # Cache operations
    # ─────────────────────────────────────────────────────────────
    
    @staticmethod
    def make_cache_key(query: str, file_hash: str, chunk_id: Optional[str] = None) -> str:
        """
        Generate a deterministic cache key.
        
        Args:
            query: The query text
            file_hash: Hash of the source file
            chunk_id: Optional chunk identifier
        """
        content = f"{file_hash}:{query}"
        if chunk_id:
            content += f":{chunk_id}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    async def cache_get(self, key: str) -> Optional[str]:
        """
        Get a cached value.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT cache_value FROM query_cache 
                WHERE cache_key = $1 
                AND (expires_at IS NULL OR expires_at > NOW())
                """,
                key
            )
            return row["cache_value"] if row else None
    
    async def cache_set(
        self,
        key: str,
        value: str,
        file_hash: str,
        ttl: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Set a cached value.
        
        Args:
            key: Cache key
            value: Value to cache
            file_hash: Hash of source file (for invalidation)
            ttl: Time-to-live in seconds (None = no expiration)
            metadata: Optional metadata dict
        """
        expires_at = None
        if ttl:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO query_cache (cache_key, cache_value, file_hash, expires_at, metadata)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (cache_key) DO UPDATE SET
                    cache_value = EXCLUDED.cache_value,
                    expires_at = EXCLUDED.expires_at,
                    metadata = EXCLUDED.metadata
                """,
                key,
                value,
                file_hash,
                expires_at,
                json.dumps(metadata or {}),
            )
    
    async def cache_invalidate_file(self, file_hash: str) -> int:
        """
        Invalidate all cache entries for a file.
        
        Args:
            file_hash: Hash of the file
            
        Returns:
            Number of entries deleted
        """
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM query_cache WHERE file_hash = $1",
                file_hash
            )
            return int(result.split()[-1])
    
    async def cache_cleanup_expired(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            Number of entries deleted
        """
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM query_cache WHERE expires_at < NOW()"
            )
            return int(result.split()[-1])
    
    # ─────────────────────────────────────────────────────────────
    # Session operations
    # ─────────────────────────────────────────────────────────────
    
    async def session_create(
        self,
        session_id: str,
        file_path: str,
        schema_json: dict,
        metadata: Optional[dict] = None,
    ) -> None:
        """Create or update a session."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO sessions (session_id, file_path, schema_json, metadata)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (session_id) DO UPDATE SET
                    file_path = EXCLUDED.file_path,
                    schema_json = EXCLUDED.schema_json,
                    last_accessed = NOW(),
                    metadata = EXCLUDED.metadata
                """,
                session_id,
                file_path,
                json.dumps(schema_json),
                json.dumps(metadata or {}),
            )
    
    async def session_get(self, session_id: str) -> Optional[dict]:
        """Get session data."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE sessions SET last_accessed = NOW()
                WHERE session_id = $1
                RETURNING file_path, schema_json, created_at, metadata
                """,
                session_id
            )
            if not row:
                return None
            
            return {
                "session_id": session_id,
                "file_path": row["file_path"],
                "schema": json.loads(row["schema_json"]),
                "created_at": row["created_at"].isoformat(),
                "metadata": json.loads(row["metadata"]),
            }
    
    async def session_delete(self, session_id: str) -> bool:
        """Delete a session and its traces."""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM sessions WHERE session_id = $1",
                session_id
            )
            return result.split()[-1] != "0"
    
    # ─────────────────────────────────────────────────────────────
    # Trace operations
    # ─────────────────────────────────────────────────────────────
    
    async def trace_save(
        self,
        trace_id: str,
        session_id: str,
        query: str,
        trace_json: dict,
        tokens_used: int = 0,
        duration_ms: float = 0,
    ) -> None:
        """Save an execution trace."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO execution_traces 
                (trace_id, session_id, query, trace_json, tokens_used, duration_ms)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                trace_id,
                session_id,
                query,
                json.dumps(trace_json),
                tokens_used,
                duration_ms,
            )
    
    async def trace_get(self, trace_id: str) -> Optional[dict]:
        """Get a trace by ID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT trace_id, session_id, query, trace_json, 
                       tokens_used, duration_ms, created_at
                FROM execution_traces WHERE trace_id = $1
                """,
                trace_id
            )
            if not row:
                return None
            
            return {
                "trace_id": row["trace_id"],
                "session_id": row["session_id"],
                "query": row["query"],
                "trace": json.loads(row["trace_json"]),
                "tokens_used": row["tokens_used"],
                "duration_ms": row["duration_ms"],
                "created_at": row["created_at"].isoformat(),
            }
    
    async def traces_list(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[dict]:
        """List traces for a session."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT trace_id, query, tokens_used, duration_ms, created_at
                FROM execution_traces
                WHERE session_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                session_id,
                limit,
            )
            return [
                {
                    "trace_id": row["trace_id"],
                    "query": row["query"],
                    "tokens_used": row["tokens_used"],
                    "duration_ms": row["duration_ms"],
                    "created_at": row["created_at"].isoformat(),
                }
                for row in rows
            ]

