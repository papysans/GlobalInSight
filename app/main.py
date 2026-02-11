import sys
import asyncio
import logging
import warnings

# 过滤 Pydantic 的字段名冲突警告（来自第三方库，不影响功能）
warnings.filterwarnings("ignore", message="Field name.*shadows an attribute in parent.*", category=UserWarning)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Force ProactorEventLoop on Windows for Playwright compatibility
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        logger.info("✅ WindowsProactorEventLoopPolicy applied successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to set WindowsProactorEventLoopPolicy: {e}")

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.api.endpoints import router
from app.api.stock_endpoints import router as stock_router
from app.api.content_endpoints import router as content_router
from app.api.sentiment_endpoints import router as sentiment_router
from app.services.scheduler_service import scheduler_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 启动定时调度服务（每日速报 + 增量检查）...")
    scheduler_service.start(daily_hour=18, daily_minute=0)
    
    yield
    
    # 关闭时执行
    logger.info("🛑 停止定时调度服务...")
    scheduler_service.stop()


app = FastAPI(
    title="News Opinion Analysis System",
    lifespan=lifespan
)

# CORS is crucial for Vue frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev, restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(stock_router, prefix="/api/stock")
app.include_router(content_router, prefix="/api/content")
app.include_router(sentiment_router, prefix="/api/sentiment")

# SPA catch-all: serve dist/index.html for all non-API routes (production)
DIST_DIR = Path(__file__).resolve().parent.parent / "dist"

if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        """Serve Vue SPA index.html for all non-API routes."""
        file_path = DIST_DIR / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(DIST_DIR / "index.html"))

if __name__ == "__main__":
    import uvicorn
    # Disable reload to prevent subprocesses from resetting the EventLoopPolicy on Windows
    # Pass the app instance directly
    logger.info(f"🔒 Current Event Loop Policy: {asyncio.get_event_loop_policy()}")
    uvicorn.run(app, host="0.0.0.0", port=8000, loop="asyncio")
