import logging

import socketio


logger = logging.getLogger(__name__)


def register_socketio_events(sio: socketio.AsyncServer) -> None:
    @sio.event
    async def connect(sid, environ, auth=None):
        logger.info("Socket.IO Client connected: %s", sid)
        if auth:
            logger.info("Auth data: %s", auth)
        return True

    @sio.event
    async def disconnect(sid):
        logger.info("Client disconnected: %s", sid)

    @sio.event
    async def typing(sid, data):
        try:
            await sio.emit("typing", data, skip_sid=sid)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Error in typing event: %s", exc)

    @sio.event
    async def connect_error(sid, data):
        logger.error("Socket.IO connection error for %s: %s", sid, data)
