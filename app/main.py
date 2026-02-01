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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.endpoints import router
from app.services.hot_news_scheduler import hot_news_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 启动热点新闻定时任务...")
    # 使用配置中的刷新间隔（默认 4 小时）
    hot_news_scheduler.start()
    
    yield
    
    # 关闭时执行
    logger.info("🛑 停止热点新闻定时任务...")
    hot_news_scheduler.stop()


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

if __name__ == "__main__":
    import uvicorn
    # Disable reload to prevent subprocesses from resetting the EventLoopPolicy on Windows
    # Pass the app instance directly
    logger.info(f"🔒 Current Event Loop Policy: {asyncio.get_event_loop_policy()}")
    uvicorn.run(app, host="0.0.0.0", port=8000, loop="asyncio")
