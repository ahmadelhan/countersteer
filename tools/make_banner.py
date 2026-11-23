"""
pip install pillow
Run from the project folder:
python tools/make_banner.py path/to/countersteer-bannerlogo.png
"""

import os
import sys

from PIL import Image

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT = os.path.join(PROJECT, "images")
SIZES = {"banner_header.png": 46}     # pixels
SPECKLE = 40                          
PAD = 4                              


def cleanBanner(path):
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    image.putalpha(alpha.point(lambda a: 0 if a < SPECKLE else a))   
    left, top, right, bottom = image.getchannel("A").getbbox()
    return image.crop((max(0, left - PAD), max(0, top - PAD),
                       min(image.width, right + PAD), min(image.height, bottom + PAD)))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("python tools/make_banner.py path/to/banner.png")
        sys.exit(1)
    banner = cleanBanner(sys.argv[1])
    for name, height in SIZES.items():
        width = round(banner.width * height / banner.height)
        banner.resize((width, height), Image.LANCZOS).save(os.path.join(OUTPUT, name), optimize=True)
        print(f"saved images/{name}  ({width} x {height})")