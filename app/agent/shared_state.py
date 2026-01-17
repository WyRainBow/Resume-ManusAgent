"""
AgentSharedState - session-scoped shared state container.
"""

from threading import RLock
from typing import Any, Dict, Optional


class AgentSharedState:
    """Thread-safe shared state for a single conversation/session."""

    def __init__(self, session_id: str, initial: Optional[Dict[str, Any]] = None):
        self.session_id = session_id
        self._data: Dict[str, Any] = dict(initial or {})
        self._lock = RLock()

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def has(self, key: str) -> bool:
        with self._lock:
            return key in self._data

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False

    def update(self, data: Dict[str, Any]) -> None:
        with self._lock:
            self._data.update(data)

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._data)
