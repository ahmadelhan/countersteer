"""
pip install pillow
python tools/make_cars.py path/to/renders

one folder, per car render renders/s15/s15_0001.png
"""
import os
import sys

from PIL import Image, ImageChops, ImageEnhance, ImageFilter

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)
import theme

OUTPUT = os.path.join(PROJECT, "images", "cars")
SIZES = {"garage": (480, 210), "draft": (340, 145)}    
STYLES = ["real", "neon"]
PAD = 14


def hexToRgb(colour):
    colour = colour.lstrip("#")
    return tuple(int(colour[i:i + 2], 16) for i in (0, 2, 4))


def loadFrames(folder):
    names = sorted(n for n in os.listdir(folder) if n.lower().endswith(".png"))
    return [Image.open(os.path.join(folder, n)).convert("RGBA") for n in names]


def unionBox(frames):
    boxes = [f.getchannel("A").getbbox() for f in frames]
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def neon(image):
    alpha = image.getchannel("A")

    glowMask = alpha.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(7))
    glow = Image.new("RGBA", image.size, hexToRgb(theme.pink) + (0,))
    glow.putalpha(glowMask.point(lambda a: int(a * 0.8)))

    rimMask = ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(3)), alpha)
    rim = Image.new("RGBA", image.size, hexToRgb(theme.cyan) + (0,))
    rim.putalpha(rimMask)

    car = ImageEnhance.Brightness(image).enhance(0.85)
    out = Image.alpha_composite(glow, car)
    return Image.alpha_composite(out, rim)


def processCar(folder, outFolder):
    frames = loadFrames(folder)
    left, top, right, bottom = unionBox(frames)
    cropW, cropH = right - left, bottom - top
    os.makedirs(outFolder, exist_ok=True)

    for sizeName, (maxW, maxH) in SIZES.items():
        scale = min((maxW - PAD * 2) / cropW, (maxH - PAD * 2) / cropH)
        newW, newH = round(cropW * scale), round(cropH * scale)
        for number, frame in enumerate(frames, start=1):
            small = frame.crop((left, top, right, bottom)).resize((newW, newH), Image.LANCZOS)
            padded = Image.new("RGBA", (newW + PAD * 2, newH + PAD * 2), (0, 0, 0, 0))
            padded.paste(small, (PAD, PAD))
            for style in STYLES:
                result = neon(padded) if style == "neon" else padded
                result.save(os.path.join(outFolder, f"{style}_{sizeName}_{number:02d}.png"),
                            optimize=True)
        print(f"  {sizeName:6} {newW + PAD * 2} x {newH + PAD * 2}")
    return len(frames)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("python tools/make_cars.py path/to/renders")
        sys.exit(1)
    renders = sys.argv[1]
    for car in sorted(os.listdir(renders)):
        folder = os.path.join(renders, car)
        if os.path.isdir(folder):
            print(car)
            count = processCar(folder, os.path.join(OUTPUT, car))
            print(f"  {count} frames done")