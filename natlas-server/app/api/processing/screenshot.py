import base64
import hashlib
import os
from io import BytesIO

from flask import current_app
from PIL import Image, UnidentifiedImageError


def is_valid_image(path: str) -> bool:
    try:
        Image.open(path)
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


def get_file_path(img_hash: str, subdir: str, ext: str) -> str:
    hash_path = f"{img_hash[0:2]}/{img_hash[2:4]}"
    hash_dir = os.path.join(current_app.config["MEDIA_DIRECTORY"], subdir, hash_path)
    os.makedirs(hash_dir, exist_ok=True)
    return os.path.join(hash_dir, img_hash + ext)


def create_thumbnail(fname, file_ext):  # type: ignore[no-untyped-def]
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

    if not is_valid_image(BytesIO(image)):  # type: ignore[arg-type]
        return {}

    image_hash = hashlib.sha256(image).hexdigest()
    fname = get_file_path(image_hash, "original", file_ext)

    with open(fname, "wb") as f:
        f.write(image)

    screenshot["hash"] = image_hash
    screenshot["thumb_hash"] = create_thumbnail(fname, file_ext)

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
