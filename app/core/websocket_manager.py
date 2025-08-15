import asyncio
from asyncio import AbstractEventLoop
from typing import Dict, Set, Optional, Coroutine, Any
from fastapi import WebSocket

class ConnectionManager:
    """
    Tracks active WebSocket connections per user id.
    """
    def __init__(self) -> None:
        # user_id -> set of websockets
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # simple lock to serialize map mutations
        self._lock = asyncio.Lock()
        # main application loop for cross-thread scheduling
        self._loop: Optional[AbstractEventLoop] = None

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.setdefault(user_id, set()).add(websocket)

    async def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            conns = self.active_connections.get(user_id)
            if conns and websocket in conns:
                conns.remove(websocket)
                if not conns:
                    self.active_connections.pop(user_id, None)

    async def send_json_to_user(self, user_id: int, message: dict) -> None:
        async with self._lock:
            conns = list(self.active_connections.get(user_id, set()))
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                # Best-effort send; ignore broken sockets
                pass

    async def broadcast_json(self, message: dict) -> None:
        async with self._lock:
            all_conns = [ws for conns in self.active_connections.values() for ws in conns]
        for ws in all_conns:
            try:
                await ws.send_json(message)
            except Exception:
                pass

    def set_event_loop(self, loop: AbstractEventLoop) -> None:
        """Set the main event loop so background threads can schedule tasks safely."""
        self._loop = loop

    def run_in_loop(self, coro: Coroutine[Any, Any, Any]) -> None:
        """Schedule a coroutine to run on the stored loop from any thread.

        If no loop is stored, this is a no-op.
        """
        if self._loop is None:
            return
        try:
            asyncio.run_coroutine_threadsafe(coro, self._loop)
        except Exception:
            # Best-effort; ignore scheduling errors
            pass

# Singleton instance
manager = ConnectionManager()
