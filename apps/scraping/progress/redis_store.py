import json
import asyncio
from typing import Dict, Any, Optional

class ProgressTracker:
    """
    Manages progress state, designed to be backed by Redis.
    For this implementation, we default to in-memory if Redis is not configured,
    or we can print to stdout for CLI usage.
    """
    def __init__(self, redis_client=None, task_id: str = "default"):
        self.redis = redis_client
        self.task_id = task_id
        self._local_state = {}

    async def emit_progress(self, phase: str, percent: int, message: str, metadata: Dict[str, Any] = None) -> None:
        """
        Update progress.
        """
        if metadata is None:
            metadata = {}

        state = {
            "phase": phase,
            "percent": percent,
            "message": message,
            "metadata": metadata
            # "timestamp": datetime.utcnow().isoformat()
        }
        
        # Update local state
        self._local_state = state
        
        # Print to console (CLI mode)
        emoji_map = {
            "loading": "⏳",
            "detecting": "🔍",
            "scraping": "⬇️",
            "finalizing": "🎬",
            "generating": "📊",
            "complete": "✅",
            "error": "❌"
        }
        icon = emoji_map.get(phase, "ℹ️")
        print(f"{icon} [{percent}%] {message}")

        # If Redis is available, publish/set
        if self.redis:
            try:
                await self.redis.set(f"task:{self.task_id}:progress", json.dumps(state))
                await self.redis.publish(f"task:{self.task_id}:updates", json.dumps(state))
            except Exception:
                pass # Ignore redis errors in fallback mode

    async def get_progress(self) -> Dict[str, Any]:
        if self.redis:
            try:
                val = await self.redis.get(f"task:{self.task_id}:progress")
                if val:
                    return json.loads(val)
            except Exception:
                pass
        return self._local_state
