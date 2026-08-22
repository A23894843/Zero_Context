import os
import logging
import aiomysql
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Security, Request
from fastapi.security import APIKeyHeader
from fastapi.templating import Jinja2Templates
import config
from engine.log_setup import setup_logging

setup_logging(config.TEMP_DIR)
log = logging.getLogger("zero_context.dashboard")

db_pool = None

# --- Auth ---------------------------------------------------------------
# Simple API-key gate for the alerts endpoint. The dashboard page itself
# stays public so the frontend can load, but the data feed requires a key.
# Set ZC_DASHBOARD_API_KEY in your .env; requests must send it as the
# `X-API-Key` header.
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str = Security(_api_key_header)):
    expected = os.getenv("ZC_DASHBOARD_API_KEY")
    if not expected:
        # No key configured: fail closed rather than silently exposing data.
        log.error("ZC_DASHBOARD_API_KEY is not set — refusing all alert requests.")
        raise HTTPException(status_code=503, detail="Dashboard API key not configured on server.")
    if api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the database connection pool tied to the FastAPI server lifecycle."""
    global db_pool
    db_pool = await aiomysql.create_pool(
        host=config.DB_HOST,
        port=3306,
        user=config.DB_USER,
        password=config.DB_PASS,
        db=config.DB_NAME,
        autocommit=True,
        minsize=1,
        maxsize=5,
    )
    log.info("Dashboard database pool initialized.")
    yield
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()
        log.info("Dashboard database pool closed.")


app = FastAPI(title="ZeroContext SOC Dashboard", lifespan=lifespan)
templates = Jinja2Templates(directory=os.path.join(config.BASE_DIR, "templates"))


@app.get("/")
async def serve_dashboard(request: Request):
    # Inject the API key server-side so index.html's JS can attach it to
    # fetch('/api/alerts') as the X-API-Key header. This keeps the key out
    # of the static file itself while still letting the same-origin page
    # authenticate against the endpoint we locked down.
    api_key = os.getenv("ZC_DASHBOARD_API_KEY", "")
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"request": request, "zc_api_key": api_key}
    )


@app.get("/api/alerts")
async def get_recent_alerts(_: bool = Depends(require_api_key)):
    alerts = []
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as curr:
                    await curr.execute("SELECT * FROM threat_alerts ORDER BY timestamp DESC LIMIT 50")
                    alerts = await curr.fetchall()
        except Exception as e:
            log.error(f"Dashboard database error: {e}")
    return alerts


if __name__ == "__main__":
    import uvicorn
    # Change host to "0.0.0.0" so Docker can expose it
    uvicorn.run("dashboard:app", host="0.0.0.0", port=config.DASHBOARD_PORT, reload=False)