import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from app.models.schemas import BlendSession

logger = logging.getLogger("blend.persistence")

class BlendPersistenceManager:
    """
    Lightweight, atomic JSON-based file persistence for Blend rooms.
    Ensures that rooms, member constraints, outfits, and harmony scores
    persist across server restarts and crashes without heavy external databases.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        if storage_dir is None:
            # Default to backend/data/blend_rooms
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            self.storage_dir = base_dir / "data" / "blend_rooms"
        else:
            self.storage_dir = Path(storage_dir)

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, BlendSession] = {}
        self._load_all_on_startup()

    def _get_file_path(self, blend_id: str) -> Path:
        # Sanitize blend_id to prevent path traversal
        clean_id = "".join(c for c in blend_id if c.isalnum() or c in ("-", "_"))
        return self.storage_dir / f"{clean_id}.json"

    def _load_all_on_startup(self) -> None:
        """Loads all existing room JSON files into in-memory cache."""
        try:
            for file_path in self.storage_dir.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        session = BlendSession(**data)
                        self._cache[session.blend_id] = session
                except Exception as e:
                    logger.warning(f"Could not load room from {file_path.name}: {e}")
        except Exception as e:
            logger.warning(f"Error scanning blend persistence directory: {e}")

    def save(self, session: BlendSession) -> None:
        """Saves a BlendSession to both in-memory cache and atomic disk file."""
        self._cache[session.blend_id] = session
        file_path = self._get_file_path(session.blend_id)

        try:
            # Atomic write via temp file
            temp_path = file_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(session.model_dump(), f, indent=2, default=str)
            temp_path.replace(file_path)
        except Exception as e:
            logger.error(f"Failed to persist blend room {session.blend_id} to disk: {e}")

    def get(self, blend_id: str) -> Optional[BlendSession]:
        """Retrieves a room by ID from cache or disk."""
        if blend_id in self._cache:
            return self._cache[blend_id]

        file_path = self._get_file_path(blend_id)
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    session = BlendSession(**data)
                    self._cache[session.blend_id] = session
                    return session
            except Exception as e:
                logger.error(f"Failed reading room file {file_path.name}: {e}")

        return None

    def list_all(self) -> List[BlendSession]:
        """Returns all persisted sessions."""
        return list(self._cache.values())

    def delete(self, blend_id: str) -> bool:
        """Deletes a session from cache and disk."""
        self._cache.pop(blend_id, None)
        file_path = self._get_file_path(blend_id)
        if file_path.exists():
            try:
                file_path.unlink()
                return True
            except Exception as e:
                logger.error(f"Failed deleting room file {file_path.name}: {e}")
        return False
