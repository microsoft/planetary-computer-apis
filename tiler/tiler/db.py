"""Database connection handling."""
import logging
from threading import Semaphore
from typing import Any, Callable, TypeVar

from fastapi import FastAPI
from psycopg2 import InterfaceError, OperationalError, pool
from titiler.pgstac.settings import PostgresSettings

settings = PostgresSettings()

logger = logging.getLogger(__name__)

# Use a semiphore to block until connections are available
# https://stackoverflow.com/a/53437049/841563

Connection = Any
"""pgsycopg2 connection can't be used as a type. Alias for readability"""

T = TypeVar("T")


class BlockingThreadedConnectionPool(pool.ThreadedConnectionPool):
    def __init__(self, minconn: int, maxconn: int, *args: Any, **kwargs: Any) -> None:
        self._semaphore = Semaphore(maxconn)
        super().__init__(minconn, maxconn, *args, **kwargs)

    def getconn(self, *args: Any, **kwargs: Any) -> Any:
        self._semaphore.acquire()
        conn = super().getconn(*args, **kwargs)
        if conn.closed:
            super().putconn(conn, close=True)
            conn = super().getconn(*args, **kwargs)
        return conn

    def putconn(self, *args: Any, **kwargs: Any) -> None:
        super().putconn(*args, **kwargs)
        self._semaphore.release()


async def connect_to_db(app: FastAPI) -> None:
    """Connect to Database."""
    pool = BlockingThreadedConnectionPool(
        minconn=settings.db_min_conn_size,
        maxconn=settings.db_max_conn_size,
        dsn=settings.reader_connection_string,
        options="-c search_path=pgstac,public -c application_name=pgstac",
    )
    # Reader and writer use same connection pool,
    # to keep connections down. Keep the two variables
    # as titiler-pgstac expects both.
    app.state.readpool = pool
    app.state.writepool = pool


async def close_db_connection(app: FastAPI) -> None:
    """Close connection."""
    # Only close the one, since they are the same
    app.state.readpool.closeall()


def with_retry_connection(
    pool: pool.ThreadedConnectionPool, fn: Callable[[Connection], T]
) -> T:

    conn = pool.getconn()
    first_try_fail = False

    try:

        return fn(conn)
    except (OperationalError, InterfaceError):
        # Close out this connection, get a new one, try again.
        logger.warning("CONNECTION FAILED - RETRYING")
        try:
            if not conn.closed:
                conn.close()
        except Exception:
            conn.closed = 2

        pool.putconn(conn)
        first_try_fail = True

        conn2 = pool.getconn()
        try:
            return fn(conn2)
        finally:
            pool.putconn(conn2)

    finally:
        if not first_try_fail:
            pool.putconn(conn)
