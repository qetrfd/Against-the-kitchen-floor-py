from __future__ import annotations

import math
import random
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


def _font(size: int, italic: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf" if italic else
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
        "/System/Library/Fonts/Supplemental/Baskerville.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf" if italic else
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def _contain(path: Path, box: tuple[int, int], opacity: int = 255) -> Image.Image | None:
    if not path.exists():
        return None
    try:
        image = Image.open(path).convert("RGBA")
        image.thumbnail(box, Image.Resampling.LANCZOS)
        if opacity < 255:
            image.putalpha(image.getchannel("A").point(lambda a: a * opacity // 255))
        return image
    except OSError:
        return None


def render_background(
    size: tuple[int, int], assets_dir: Path, palette: dict[str, str], seed: int
) -> Image.Image:
    width, height = size
    rng = random.Random(seed)
    background = Image.new("RGB", size, palette["soft_black"])
    draw = ImageDraw.Draw(background, "RGBA")

    # Telón oscuro con resplandor central y viñeta.
    for radius in range(max(width, height), 0, -18):
        ratio = radius / max(width, height)
        alpha = int(12 * (1 - ratio))
        color = palette["wine"] if radius % 36 else palette["coffee"]
        draw.ellipse(
            (width / 2 - radius, height / 2 - radius * .7,
             width / 2 + radius, height / 2 + radius * .7),
            fill=(*ImageColor_getrgb(color), alpha),
        )

    texture_path = assets_dir / "paper_texture.png"
    if texture_path.exists():
        texture = ImageOps.fit(Image.open(texture_path).convert("RGB"), size)
        texture = ImageEnhance.Contrast(texture).enhance(1.25)
        texture = ImageEnhance.Brightness(texture).enhance(.42)
        background = Image.blend(background, texture, .22)

    canvas = background.convert("RGBA")
    # Portada como póster central; el marco entregado se coloca encima.
    cover = _contain(assets_dir / "cover.jpeg", (int(height * .55), int(height * .55)), 210)
    if cover:
        cover = ImageEnhance.Contrast(cover).enhance(1.08)
        x, y = (width - cover.width) // 2, (height - cover.height) // 2
        shadow = Image.new("RGBA", (cover.width + 50, cover.height + 50), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rectangle((25, 25, cover.width + 25, cover.height + 25), fill=(0, 0, 0, 170))
        shadow = shadow.filter(ImageFilter.GaussianBlur(18))
        canvas.alpha_composite(shadow, (x - 25, y - 15))
        canvas.alpha_composite(cover, (x, y))

        frame = _contain(assets_dir / "ornate_frame.png", (cover.width + 110, cover.height + 110), 235)
        if frame:
            frame = frame.resize((cover.width + 80, cover.height + 80), Image.Resampling.LANCZOS)
            canvas.alpha_composite(frame, (x - 40, y - 40))

    decorations = [
        ("sun.png", (int(width * .25), int(width * .25)), (int(width * .78), int(height * .70)), 145),
        ("moon.png", (int(width * .18), int(height * .44)), (int(width * .02), int(height * .06)), 150),
        ("rose.png", (int(width * .17), int(height * .62)), (int(width * .06), int(height * .42)), 150),
    ]
    for name, box, position, opacity in decorations:
        image = _contain(assets_dir / name, box, opacity)
        if image:
            canvas.alpha_composite(image, position)

    draw = ImageDraw.Draw(canvas, "RGBA")
    for _ in range(int(width * height / 1050)):
        x, y = rng.randrange(width), rng.randrange(height)
        tone = rng.choice([(229, 202, 145), (60, 28, 24), (109, 142, 130)])
        draw.point((x, y), fill=(*tone, rng.randrange(12, 44)))
    draw.rectangle((18, 18, width - 19, height - 19), outline=(*ImageColor_getrgb(palette["gold"]), 120), width=2)
    draw.rectangle((25, 25, width - 26, height - 26), outline=(*ImageColor_getrgb(palette["wine"]), 170), width=1)
    return canvas.convert("RGB")


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def render_card(
    text: str,
    number: int,
    size: tuple[int, int],
    assets_dir: Path,
    palette: dict[str, str],
    seed: int,
) -> Image.Image:
    width, height = size
    rng = random.Random(seed + number * 73)
    base = Image.new("RGB", size, palette["paper"])
    texture_path = assets_dir / "paper_texture.png"
    if texture_path.exists():
        texture = ImageOps.fit(Image.open(texture_path).convert("RGB"), size)
        texture = ImageEnhance.Brightness(texture).enhance(1.08)
        base = Image.blend(base, texture, .34)

    draw = ImageDraw.Draw(base, "RGBA")
    # Bordes irregulares, manchas y grano artesanal.
    for _ in range(90):
        x, y = rng.randrange(width), rng.randrange(height)
        radius = rng.randrange(1, 12)
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=(83, 49, 31, rng.randrange(3, 16)))
    draw.rounded_rectangle((8, 8, width - 9, height - 9), radius=15,
                           outline=(*ImageColor_getrgb(palette["coffee"]), 230), width=4)
    draw.rounded_rectangle((17, 17, width - 18, height - 18), radius=11,
                           outline=(*ImageColor_getrgb(palette["gold"]), 210), width=2)
    draw.line((42, 45, width - 42, 45), fill=(*ImageColor_getrgb(palette["wine"]), 190), width=2)
    draw.polygon([(width//2-6, 40), (width//2, 34), (width//2+6, 40), (width//2, 46)],
                 fill=palette["burnt_red"])

    font_size = 46 if len(text) < 48 else 38 if len(text) < 85 else 32
    font_size = max(24, int(font_size * min(1.0, width / 620)))
    font = _font(font_size, italic=(number % 3 == 1))
    lines = _wrap_text(draw, text, font, width - 92)
    boxes = [draw.textbbox((0, 0), line, font=font) for line in lines]
    line_height = max((box[3] - box[1] for box in boxes), default=font_size) + 9
    total_height = line_height * len(lines)
    y = max(67, (height - total_height) // 2)
    for line, box in zip(lines, boxes):
        text_width = box[2] - box[0]
        x = (width - text_width) // 2
        draw.text((x + 2, y + 2), line, font=font, fill=(255, 246, 220, 90))
        draw.text((x, y), line, font=font, fill=palette["ink"], stroke_width=1,
                  stroke_fill=palette["coffee"])
        y += line_height

    small_font = _font(15)
    # Solo caracteres presentes incluso en las fuentes serif más antiguas.
    footer = f"—  {number:02d}  —"
    footer_box = draw.textbbox((0, 0), footer, font=small_font)
    draw.text(((width - footer_box[2]) // 2, height - 39), footer, font=small_font,
              fill=palette["wine"])
    return base


def ImageColor_getrgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))


def ease_out_cubic(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return 1 - (1 - value) ** 3


def ease_in_out(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return -(math.cos(math.pi * value) - 1) / 2
