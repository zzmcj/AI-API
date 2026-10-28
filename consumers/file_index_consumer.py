import io
import json
import logging
from pathlib import Path
from urllib.parse import urlparse

import pika
from minio import Minio
from PyPDF2 import PdfReader

from core.config import settings
from tools.file_parse import ocr_image_bytes, ocr_pdf_page_images, parse_docx_bytes
from services.file_index_store import already_done, mark
from services.vector_store import save_chunks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def build_minio_client() -> Minio:
    parsed = urlparse(settings.MINIO_ENDPOINT)
    return Minio(
        parsed.netloc,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=parsed.scheme == "https",
    )


def download_object(client: Minio, bucket: str, object_key: str) -> bytes:
    response = client.get_object(bucket, object_key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def recognize_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
        image_text = ocr_pdf_page_images(page)
        if image_text:
            parts.append(image_text)
    return "\n\n".join(part for part in parts if part.strip())


def recognize(file_name: str, data: bytes) -> str:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".pdf":
        return recognize_pdf(data)
    if suffix == ".docx":
        return parse_docx_bytes(data)
    if suffix in IMAGE_SUFFIXES:
        return ocr_image_bytes(data)
    if suffix in {".txt", ".md"}:
        return data.decode("utf-8")
    raise ValueError(f"暂不识别该类型: {suffix}")

def index_file(minio_client: Minio, bucket: str, object_key: str, file_name: str, file_id: int) -> None:
    data = download_object(minio_client, bucket, object_key)
    text = recognize(file_name, data)
    logging.info(
        "识别完成 objectKey=%s bytes=%s chars=%s preview=%s",
        object_key,
        len(data),
        len(text),
        text[:200].replace("\n", " "),
    )
    save_chunks(file_id, text)
def on_message(channel, method, properties, body, minio_client: Minio):
    message = json.loads(body.decode("utf-8"))
    file_id = int(message["fileId"])
    object_key = message["objectKey"]
    if already_done(file_id):
        channel.basic_ack(method.delivery_tag)
        return
    try:
      index_file(minio_client, message["bucket"], object_key, message["fileName"], file_id)
      mark(file_id, object_key, "done")
      channel.basic_ack(method.delivery_tag)
    except Exception as exc:
        mark(file_id, object_key, "failed", str(exc)[:1000])
        channel.basic_nack(method.delivery_tag, requeue=False)


def main():
    minio_client = build_minio_client()
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_USERNAME,
        settings.RABBITMQ_PASSWORD,
    )
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=credentials,
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue=settings.FILE_INDEX_QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue=settings.FILE_INDEX_QUEUE,
        on_message_callback=lambda ch, method, properties, body: on_message(
            ch, method, properties, body, minio_client
        ),
        auto_ack=False,
    )
    logging.info("开始消费队列 %s", settings.FILE_INDEX_QUEUE)
    channel.start_consuming()


if __name__ == "__main__":
    main()