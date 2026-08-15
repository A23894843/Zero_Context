import os
import aiomysql
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
import config

db_pool = None

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
        maxsize=5
    )
    print("[+] Dashboard Database Pool Initialized.")
    yield
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()
        print("[-] Dashboard Database Pool Closed.")

app = FastAPI(title="ZeroContext SOC Dashboard", lifespan=lifespan)

@app.get("/")
async def serve_dashboard():
    template_path = os.path.join(config.BASE_DIR, "templates", "index.html")
    return FileResponse(template_path)

@app.get("/api/alerts")
async def get_recent_alerts():
    alerts = []
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as curr:
                    await curr.execute("SELECT * FROM threat_alerts ORDER BY timestamp DESC LIMIT 50")
                    alerts = await curr.fetchall()
        except Exception as e:
            print(f"[!] Dashboard Database Error: {e}")
    return alerts