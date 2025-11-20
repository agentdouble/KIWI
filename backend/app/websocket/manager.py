from typing import Iterable, List

import socketio


def create_socket_server(cors_allowed_origins: Iterable[str]) -> socketio.AsyncServer:
    origins: List[str] = list(cors_allowed_origins)
    return socketio.AsyncServer(
        cors_allowed_origins=origins,
        async_mode="asgi",
        logger=False,
        engineio_logger=False,
    )


def create_socket_app(sio: socketio.AsyncServer) -> socketio.ASGIApp:
    return socketio.ASGIApp(sio, socketio_path="/socket.io")
