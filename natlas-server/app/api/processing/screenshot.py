from flask import current_app
import base64
import hashlib
import os
from PIL import Image


def create_thumbnail(fname, file_ext):
    thumb_size = (255, 160)
    thumb = Image.open(fname)
    thumb.thumbnail(thumb_size)
    thumb_hash = hashlib.sha256(thumb.tobytes()).hexdigest()
    thumbhashpath = f"{thumb_hash[0:2]}/{thumb_hash[2:4]}"
    thumbpath = os.path.join(
        current_app.config["MEDIA_DIRECTORY"], "thumbs", thumbhashpath
    )
    # makedirs attempts to make every directory necessary to get to the "thumbs" folder
    os.makedirs(thumbpath, exist_ok=True)
    fname = os.path.join(thumbpath, thumb_hash + file_ext)
    thumb.save(fname)
    thumb.close()
    return thumb_hash


def process_screenshots(screenshots):
    # Handle screenshots

    num_screenshots = 0
    for item in screenshots:
        if item["service"] == "VNC":
            file_ext = ".jpg"
        else:  # Handles http, https files from aquatone/chromium-headless
            file_ext = ".png"

        image = base64.b64decode(item["data"])
        image_hash = hashlib.sha256(image).hexdigest()

        hashpath = f"{image_hash[0:2]}/{image_hash[2:4]}"
        dirpath = os.path.join(
            current_app.config["MEDIA_DIRECTORY"], "original", hashpath
        )

        # makedirs attempts to make every directory necessary to get to the "original" folder
        os.makedirs(dirpath, exist_ok=True)

        fname = os.path.join(dirpath, image_hash + file_ext)
        with open(fname, "wb") as f:
            f.write(image)
        item["hash"] = image_hash
        del item["data"]

        item["thumb_hash"] = create_thumbnail(fname, file_ext)
        num_screenshots += 1

    return screenshots, num_screenshots
