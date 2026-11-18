import os
import sys

from PIL import Image, ImageDraw, ImageFont

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)
import theme   

FONTS = os.path.join(PROJECT, "fonts")
IMAGES = os.path.join(PROJECT, "images")
DELA = os.path.join(FONTS, "DelaGothicOne-Regular.ttf")
RUSSO = os.path.join(FONTS, "RussoOne-Regular.ttf")


def renderText(text, fontPath, size, colour, slant=0.0):
    font = ImageFont.truetype(fontPath, size)
    left, top, right, bottom = font.getbbox(text)
    pad = size // 4
    width, height = right - left + pad * 2, bottom - top + pad * 2
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ImageDraw.Draw(image).text((pad - left, pad - top), text, font=font, fill=colour)

    if slant:
        extra = int(slant * height)
        image = image.transform((width + extra, height), Image.AFFINE,
                                (1, slant, -extra, 0, 1, 0), resample=Image.BICUBIC)
    return image.crop(image.getbbox())  

def stack(lines, gap):
    width = max(img.width for img in lines)
    height = sum(img.height for img in lines) + gap * (len(lines) - 1)
    out = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    y = 0
    for img in lines:
        out.paste(img, ((width - img.width) // 2, y), img)
        y += img.height + gap
    return out


def save(image, name):
    path = os.path.join(IMAGES, name)
    image.save(path)
    print(f"saved {name}  ({image.width} x {image.height})")


if __name__ == "__main__":
    os.makedirs(IMAGES, exist_ok=True)
    slant = 0.22

    save(renderText("カウンター", DELA, 112, theme.pink, slant), "title.png")
    save(renderText("カウンター", DELA, 112, theme.cyan, slant), "title_glow.png")

    subtitle = stack([
        renderText("(countersteer)", RUSSO, 16, theme.muted, slant),
        renderText("a drift team manager", RUSSO, 22, theme.text, slant),
    ], gap=6)
    save(subtitle, "subtitle.png")

    save(renderText("峠", DELA, 170, theme.panel_light), "kanji.png")
