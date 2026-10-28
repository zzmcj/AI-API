import pymysql
from datetime import datetime
from core.config import settings

def already_done(file_id: int) -> bool:
    connection = pymysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DATABASE,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT status FROM rag_file_index WHERE file_id=%s", (file_id,))
            row = cursor.fetchone()
            return row is not None and row[0] == "done"
    finally:
        connection.close()

def mark(file_id: int, object_key: str, status: str, error: str | None = None) -> None:
    connection = pymysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DATABASE,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO rag_file_index (file_id, object_key, status, error, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  object_key=VALUES(object_key),
                  status=VALUES(status),
                  error=VALUES(error),
                  updated_at=VALUES(updated_at)
                """,
                (file_id, object_key, status, error, datetime.now()),
            )
        connection.commit()
    finally:
        connection.close()