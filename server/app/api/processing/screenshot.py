import base64
import hashlib
import os
from io import BytesIO

from config import S3Settings
from flask import current_app
from minio import Minio
from PIL import Image, UnidentifiedImageError


def is_valid_image(path: str | BytesIO) -> bool:
    try:
        with Image.open(path):
            return True
    except (FileNotFoundError, UnidentifiedImageError):
        return False


def get_file_ext(service: str) -> str:
    service_ext_map = {
        "VNC": ".jpg",
        "HTTP": ".png",
        "HTTPS": ".png",
        "default": ".png",
    }
    return service_ext_map.get(service, "default")


def get_file_mime_type(service: str) -> str:
    service_ext_map = {
        "VNC": "image/jpeg",
        "HTTP": "image/png",
        "HTTPS": "image/png",
        "default": "image/png",
    }
    return service_ext_map.get(service, "default")


def get_file_path(img_hash: str, subdir: str, ext: str) -> str:
    hash_path = f"{img_hash[0:2]}/{img_hash[2:4]}"
    return os.path.join(subdir, hash_path, img_hash + ext)


def create_thumbnail(fname: str, file_ext: str) -> str:
    thumb_size = (255, 160)
    thumb = Image.open(fname)
    thumb.thumbnail(thumb_size)
    thumb_hash = hashlib.sha256(thumb.tobytes()).hexdigest()
    fname = get_file_path(thumb_hash, "thumbs", file_ext)
    thumb.save(fname)
    thumb.close()
    return thumb_hash


def process_screenshot(screenshot: dict):  # type: ignore[no-untyped-def, type-arg]
    file_ext = get_file_ext(screenshot["service"])
    image = base64.b64decode(screenshot["data"])
    del screenshot["data"]

    if not is_valid_image(BytesIO(image)):
        return {}

    image_hash = hashlib.sha256(image).hexdigest()
    fname = get_file_path(image_hash, "original", file_ext)

    s3_config: S3Settings = current_app.config["S3"]
    storage = Minio(
        endpoint=s3_config.endpoint,
        access_key=s3_config.access_key.get_secret_value(),
        secret_key=s3_config.secret_key.get_secret_value(),
        secure=s3_config.use_tls,
    )
    storage.put_object(
        bucket_name=s3_config.bucket,
        object_name=fname,
        data=BytesIO(image),
        length=len(image),
        content_type=get_file_mime_type(screenshot["service"]),
    )

    thumb_size = (255, 160)
    with Image.open(BytesIO(image)) as thumb:
        thumb.thumbnail(thumb_size)
        thumb_buffer = BytesIO()
        save_format = "JPEG" if file_ext.lower() in [".jpg", ".jpeg"] else "PNG"
        thumb.save(thumb_buffer, format=save_format)
        thumb_buffer.seek(0)
        thumbbytes = thumb_buffer.getvalue()
        thumb_hash = hashlib.sha256(thumbbytes).hexdigest()
        thumb_fname = get_file_path(thumb_hash, "thumbs", file_ext)

    storage.put_object(
        bucket_name=s3_config.bucket,
        object_name=thumb_fname,
        data=BytesIO(thumbbytes),
        length=len(thumbbytes),
        content_type=get_file_mime_type(screenshot["service"]),
    )

    screenshot["hash"] = image_hash
    screenshot["thumb_hash"] = thumb_hash

    return screenshot


def process_screenshots(screenshots: list) -> tuple:  # type: ignore[type-arg]
    processed_screenshots = []
    for item in screenshots:
        screenshot = process_screenshot(item)
        if not screenshot:
            current_app.logger.warning(
                f"Received invalid image for {screenshot['hostname']} port {screenshot['port']}"
            )
            continue
        processed_screenshots.append(item)

    return processed_screenshots, len(processed_screenshots)
