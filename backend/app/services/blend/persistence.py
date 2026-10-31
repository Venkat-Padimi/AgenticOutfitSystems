import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Optional, List
from app.models.schemas import BlendSession
from app.config import settings

logger = logging.getLogger("blend.persistence")

class BlendPersistenceManager:
    """
    Robust, thread-safe, and ACID-compliant persistence for Blend group rooms.
    Supports:
    1. SQLite (default, standard library, WAL mode) with configurable file path or persistent disk mount.
    2. PostgreSQL (Render / cloud databases via DATABASE_URL) when psycopg is available.
    3. In-memory caching for low latency reads.
    4. Auto-migration of legacy JSON room files into the database.
    """

    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        database_url: Optional[str] = None
    ):
        self._cache: Dict[str, BlendSession] = {}
        self.database_url = database_url or settings.database_url
        self.is_postgres = False

        if self.database_url and (
            self.database_url.startswith("postgres://") or self.database_url.startswith("postgresql://")
        ):
            # Render PostgreSQL connection
            try:
                import psycopg
                self.pg_conn_str = self.database_url.replace("postgres://", "postgresql://", 1)
                self.is_postgres = True
                self._init_postgres()
                logger.info("BlendPersistenceManager initialized with PostgreSQL storage.")
            except ImportError:
                logger.warning("psycopg is not installed. Falling back to SQLite persistence.")
                self.is_postgres = False
            except Exception as e:
                logger.warning(f"Failed to connect to PostgreSQL ({e}). Falling back to SQLite.")
                self.is_postgres = False

        if not self.is_postgres:
            # SQLite Mode: Determine DB Path
            if storage_dir is not None:
                self.storage_dir = Path(storage_dir)
                self.db_path = self.storage_dir / "blend.db"
            elif settings.persistence_dir:
                self.storage_dir = Path(settings.persistence_dir)
                self.db_path = self.storage_dir / "blend.db"
            elif self.database_url and self.database_url.startswith("sqlite:///"):
                raw_path = self.database_url.replace("sqlite:///", "")
                self.db_path = Path(raw_path)
                self.storage_dir = self.db_path.parent
            else:
                base_dir = Path(__file__).resolve().parent.parent.parent.parent
                self.storage_dir = base_dir / "data"
                self.db_path = self.storage_dir / "blend.db"

            self.storage_dir.mkdir(parents=True, exist_ok=True)
            self._init_sqlite()
            self._migrate_legacy_json_files()
            logger.info(f"BlendPersistenceManager initialized with SQLite storage at {self.db_path}.")

        self._load_all_on_startup()

    # -------------------------------------------------------------------------
    # Database Initialization
    # -------------------------------------------------------------------------

    def _init_sqlite(self) -> None:
        """Initializes SQLite schema and optimizes WAL mode for concurrent access."""
        with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS blend_sessions (
                    blend_id TEXT PRIMARY KEY,
                    title TEXT,
                    occasion TEXT,
                    status TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    data TEXT NOT NULL
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_blend_status ON blend_sessions(status);")
            conn.commit()

    def _init_postgres(self) -> None:
        """Initializes PostgreSQL table schema if not already created."""
        import psycopg
        with psycopg.connect(self.pg_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS blend_sessions (
                        blend_id VARCHAR(64) PRIMARY KEY,
                        title VARCHAR(255),
                        occasion VARCHAR(255),
                        status VARCHAR(64),
                        created_at VARCHAR(64),
                        updated_at VARCHAR(64),
                        data TEXT NOT NULL
                    );
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_blend_status ON blend_sessions(status);")
            conn.commit()

    def _migrate_legacy_json_files(self) -> None:
        """Imports any existing JSON session files from legacy directory into the database."""
        legacy_dirs = [self.storage_dir, self.storage_dir / "blend_rooms"]
        for l_dir in legacy_dirs:
            if not l_dir.exists():
                continue
            for json_file in l_dir.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                    session = BlendSession(**raw)
                    self.save(session)
                    logger.info(f"Migrated legacy room {session.blend_id} into database.")
                except Exception as e:
                    logger.debug(f"Could not migrate legacy file {json_file.name}: {e}")

    # -------------------------------------------------------------------------
    # In-memory Cache & Startup Load
    # -------------------------------------------------------------------------

    def _load_all_on_startup(self) -> None:
        """Pre-populates in-memory cache from database records."""
        try:
            records = self._db_list_all()
            for session in records:
                self._cache[session.blend_id] = session
        except Exception as e:
            logger.warning(f"Error loading persisted blend sessions on startup: {e}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def save(self, session: BlendSession) -> None:
        """Saves a BlendSession to both in-memory cache and persistent database."""
        self._cache[session.blend_id] = session
        raw_json = json.dumps(session.model_dump(), default=str)

        try:
            if self.is_postgres:
                self._pg_upsert(session, raw_json)
            else:
                self._sqlite_upsert(session, raw_json)
        except Exception as e:
            logger.error(f"Failed to persist blend room {session.blend_id} to database: {e}")

    def get(self, blend_id: str) -> Optional[BlendSession]:
        """Retrieves a room by ID from cache or database."""
        if blend_id in self._cache:
            return self._cache[blend_id]

        session = self._db_get(blend_id)
        if session:
            self._cache[session.blend_id] = session
            return session
        return None

    def list_all(self) -> List[BlendSession]:
        """Returns all persisted sessions."""
        return list(self._cache.values())

    def delete(self, blend_id: str) -> bool:
        """Deletes a session from cache and database."""
        self._cache.pop(blend_id, None)
        try:
            if self.is_postgres:
                return self._pg_delete(blend_id)
            else:
                return self._sqlite_delete(blend_id)
        except Exception as e:
            logger.error(f"Failed deleting blend room {blend_id}: {e}")
            return False

    # -------------------------------------------------------------------------
    # SQLite Operations
    # -------------------------------------------------------------------------

    def _sqlite_upsert(self, session: BlendSession, raw_json: str) -> None:
        with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
            conn.execute("""
                INSERT INTO blend_sessions (blend_id, title, occasion, status, created_at, updated_at, data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(blend_id) DO UPDATE SET
                    title=excluded.title,
                    occasion=excluded.occasion,
                    status=excluded.status,
                    created_at=excluded.created_at,
                    updated_at=excluded.updated_at,
                    data=excluded.data;
            """, (
                session.blend_id,
                session.title,
                session.occasion,
                session.status,
                str(session.created_at),
                str(session.updated_at),
                raw_json
            ))
            conn.commit()

    def _sqlite_get(self, blend_id: str) -> Optional[BlendSession]:
        with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
            cur = conn.execute("SELECT data FROM blend_sessions WHERE blend_id = ?", (blend_id,))
            row = cur.fetchone()
            if row:
                data = json.loads(row[0])
                return BlendSession(**data)
        return None

    def _sqlite_list_all(self) -> List[BlendSession]:
        results = []
        with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
            cur = conn.execute("SELECT data FROM blend_sessions ORDER BY updated_at DESC")
            for row in cur.fetchall():
                try:
                    data = json.loads(row[0])
                    results.append(BlendSession(**data))
                except Exception as e:
                    logger.warning(f"Error parsing persisted room record: {e}")
        return results

    def _sqlite_delete(self, blend_id: str) -> bool:
        with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
            cur = conn.execute("DELETE FROM blend_sessions WHERE blend_id = ?", (blend_id,))
            conn.commit()
            return cur.rowcount > 0

    # -------------------------------------------------------------------------
    # PostgreSQL Operations
    # -------------------------------------------------------------------------

    def _pg_upsert(self, session: BlendSession, raw_json: str) -> None:
        import psycopg
        with psycopg.connect(self.pg_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO blend_sessions (blend_id, title, occasion, status, created_at, updated_at, data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT(blend_id) DO UPDATE SET
                        title=EXCLUDED.title,
                        occasion=EXCLUDED.occasion,
                        status=EXCLUDED.status,
                        created_at=EXCLUDED.created_at,
                        updated_at=EXCLUDED.updated_at,
                        data=EXCLUDED.data;
                """, (
                    session.blend_id,
                    session.title,
                    session.occasion,
                    session.status,
                    str(session.created_at),
                    str(session.updated_at),
                    raw_json
                ))
            conn.commit()

    def _pg_get(self, blend_id: str) -> Optional[BlendSession]:
        import psycopg
        with psycopg.connect(self.pg_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT data FROM blend_sessions WHERE blend_id = %s", (blend_id,))
                row = cur.fetchone()
                if row:
                    data = json.loads(row[0])
                    return BlendSession(**data)
        return None

    def _pg_list_all(self) -> List[BlendSession]:
        import psycopg
        results = []
        with psycopg.connect(self.pg_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT data FROM blend_sessions ORDER BY updated_at DESC")
                for row in cur.fetchall():
                    try:
                        data = json.loads(row[0])
                        results.append(BlendSession(**data))
                    except Exception as e:
                        logger.warning(f"Error parsing PostgreSQL blend record: {e}")
        return results

    def _pg_delete(self, blend_id: str) -> bool:
        import psycopg
        with psycopg.connect(self.pg_conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM blend_sessions WHERE blend_id = %s", (blend_id,))
                deleted = cur.rowcount > 0
            conn.commit()
            return deleted

    # -------------------------------------------------------------------------
    # Generic DB Dispatchers
    # -------------------------------------------------------------------------

    def _db_get(self, blend_id: str) -> Optional[BlendSession]:
        if self.is_postgres:
            return self._pg_get(blend_id)
        return self._sqlite_get(blend_id)

    def _db_list_all(self) -> List[BlendSession]:
        if self.is_postgres:
            return self._pg_list_all()
        return self._sqlite_list_all()
