import asyncio
import time

import asyncpg


async def pgready():
    cnt = 0

    while True:
        if cnt > 150:
            raise Exception("Unable to connect to database")
        try:
            print(".", end="", flush=True)
            conn = await asyncpg.connect()
            await conn.execute("SELECT 1")
            await conn.close()
            return True
        except Exception:
            time.sleep(0.1)
            cnt += 1


asyncio.run(pgready())
