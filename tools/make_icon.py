"""
pip install pillow
Run from project folder:
python tools/make_icon.py path/to/icon.png
"""

import os
import sys

from PIL import Image

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(PROJECT, "images")
SIZES = [16, 32, 48, 256]


def squareIcon(path):
    image = Image.open(path).convert("RGBA")
    side = max(image.width, image.height)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(image, ((side - image.width) // 2, (side - image.height) // 2), image)
    return square


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("python tools/make_icon.py path/to/icon.png")
        sys.exit(1)
    icon = squareIcon(sys.argv[1])
    for size in SIZES:
        name = f"icon_{size}.png"
        icon.resize((size, size), Image.LANCZOS).save(os.path.join(OUTPUT, name), optimize=True)
        print(f"saved images/{name}")