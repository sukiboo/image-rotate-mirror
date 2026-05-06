import math

from PIL import Image, ImageOps


def rotate(img: Image.Image, degrees: float) -> Image.Image:
    deg = degrees % 360
    if deg == 0:
        return img.copy()
    if deg in (90, 180, 270):
        return img.rotate(deg, expand=True)
    rotated = img.rotate(deg, resample=Image.Resampling.BICUBIC, expand=True)
    return rotated.crop(inscribed_bbox(img.width, img.height, deg))


def mirror_pair(region: Image.Image) -> tuple[Image.Image, Image.Image]:
    width, height = region.size
    mid = width // 2
    left = region.crop((0, 0, mid, height))
    right = region.crop((mid, 0, width, height))

    left_out = Image.new(region.mode, (mid * 2, height))
    left_out.paste(left, (0, 0))
    left_out.paste(ImageOps.mirror(left), (mid, 0))

    right_width = width - mid
    right_out = Image.new(region.mode, (right_width * 2, height))
    right_out.paste(ImageOps.mirror(right), (0, 0))
    right_out.paste(right, (right_width, 0))

    return left_out, right_out


def inscribed_bbox(width: int, height: int, degrees: float) -> tuple[int, int, int, int]:
    # Largest axis-aligned rectangle of original-pixel content inside the rotated canvas,
    # expressed in the rotated image's coordinate frame.
    # Formula: https://stackoverflow.com/a/16778797
    angle = math.radians(degrees)
    sin_a, cos_a = abs(math.sin(angle)), abs(math.cos(angle))

    width_is_longer = width >= height
    side_long, side_short = (width, height) if width_is_longer else (height, width)
    if side_short <= 2.0 * sin_a * cos_a * side_long or abs(sin_a - cos_a) < 1e-10:
        x = 0.5 * side_short
        if width_is_longer:
            inner_w, inner_h = x / sin_a, x / cos_a
        else:
            inner_w, inner_h = x / cos_a, x / sin_a
    else:
        cos_2a = cos_a * cos_a - sin_a * sin_a
        inner_w = (width * cos_a - height * sin_a) / cos_2a
        inner_h = (height * cos_a - width * sin_a) / cos_2a

    new_w = width * cos_a + height * sin_a
    new_h = width * sin_a + height * cos_a
    x0 = round((new_w - inner_w) / 2)
    y0 = round((new_h - inner_h) / 2)
    return x0, y0, x0 + round(inner_w), y0 + round(inner_h)
