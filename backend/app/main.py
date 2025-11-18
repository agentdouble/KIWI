from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.router import api_router
from app.database import engine, Base, AsyncSessionLocal
from app.utils.rate_limit import limiter, rate_limit_exceeded_handler
from app.utils.cache import cache_service
from app.utils.schema import ensure_document_processing_schema
from slowapi.errors import RateLimitExceeded
import socketio
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

from app.utils.exceptions import AppException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    logger = logging.getLogger(__name__)
    logger.error(f"Database error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error occurred"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"}
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

@app.middleware("http")
async def log_requests(request, call_next):
    logger = logging.getLogger(__name__)
    logger.info(f"{request.method} {request.url.path}")
    logger.info(f"Headers: {dict(request.headers)}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

sio = socketio.AsyncServer(
    cors_allowed_origins=settings.cors_origins_list,
    async_mode='asgi',
    logger=False,
    engineio_logger=False
)
app.include_router(api_router, prefix="/api")
logger = logging.getLogger(__name__)
logger.info("=== Routes chargées ===")
for route in app.routes:
    if hasattr(route, 'path'):
        logger.info(f"  {route.methods} {route.path}")
logger.info("======================")
socket_app = socketio.ASGIApp(sio, socketio_path='/socket.io')
app.mount("/ws", socket_app)
logger.info("Socket.IO mounted successfully on /ws")
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await ensure_document_processing_schema()

    # Initialiser le service de cache Redis
    await cache_service.connect()

    # Garantir la présence des agents officiels
    try:
        from app.initial_data.official_agents import ensure_official_agents

        async with AsyncSessionLocal() as session:
            await ensure_official_agents(session)
    except Exception as exc:
        logger = logging.getLogger(__name__)
        logger.error("Failed to ensure official agents: %s", exc, exc_info=True)

@app.on_event("shutdown")
async def shutdown_event():
    # Fermer la connexion Redis
    await cache_service.disconnect()
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version}
@app.get("/test")
async def test():
    return {"message": "Backend is working!", "cors_origins": settings.cors_origins_list}
@app.get("/force-clear-session")
async def force_clear_session():
    return {
        "message": "Pour utiliser l'application, veuillez:",
        "steps": [
            "1. Ouvrir la console développeur (F12)",
            "2. Exécuter: localStorage.clear()",
            "3. Recharger la page (Ctrl+R ou Cmd+R)",
            "4. Une nouvelle session sera créée automatiquement"
        ]
    }

@sio.event
async def connect(sid, environ, auth=None):
    logger = logging.getLogger(__name__)
    logger.info(f"Socket.IO Client connected: {sid}")
    if auth:
        logger.info(f"Auth data: {auth}")
    return True

@sio.event
async def disconnect(sid):
    logger = logging.getLogger(__name__)
    logger.info(f"Client disconnected: {sid}")

@sio.event
async def typing(sid, data):
    try:
        await sio.emit('typing', data, skip_sid=sid)
    except Exception as e:
        logger.error(f"Error in typing event: {e}")
@sio.event
async def connect_error(sid, data):
    logger = logging.getLogger(__name__)
    logger.error(f"Socket.IO connection error for {sid}: {data}")
