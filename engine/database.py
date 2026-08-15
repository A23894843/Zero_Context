import time
from config import *
import aiomysql

class AsyncThreatDB :
    def __init__ (self, host = DB_HOST, user = DB_USER, password = DB_PASS, db = DB_NAME)   :
        """Initializes the database connection parameters."""
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        self.pool = None

    async def connect (self)    :
        """Establishes a non-blockig connection pool."""
        try :
            self.pool = await aiomysql.create_pool (
                host = self.host,
                port = 3306,
                user = self.user,
                password = self.password,
                db = self.db,
                autocommit = True,
                minsize = 1,
                maxsize = 10
            )
            print ("[+] Asynchronous MySQL Database Pool established.")
        except Exception as e :
            print (f"[!] FATAL: Failed to connect to MySQL: {e}")
            self.pool = None

    async def log_threat (self, sensor_type, anomaly_score, description) :
        """Asynchronous inserts a threat record without blokcking the UDS stream."""
        if not self.pool :
            return

        try :
            async with self.pool.acquire() as conn :
                async with conn.cursor() as cur :
                    sql = """
                        INSERT INTO threat_alerts
                        (timestamp, sensor_type, anomaly_score, description)
                        VALUES (%s, %s, %s, %s)
                    """
                    await cur.execute (sql, (time.time(), sensor_type, anomaly_score, description))

        except Exception as e :
            print (f"[!] Database Insertion Error: {e}")

    async def close (self) :
        """Safely terminatesthe connection pool during server shutdown."""
        if self.pool :
            self.pool.close()
            await self.pool.wait_closed()
            print ("[*] MySQL Connection Pool closed safely.")