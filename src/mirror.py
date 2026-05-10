from PIL import Image, ImageOps


def rotate_full(img: Image.Image, degrees: float) -> Image.Image:
    deg = degrees % 360
    if deg == 0:
        return img.copy()
    if deg in (90, 180, 270):
        return img.rotate(deg, expand=True)
    rgba = img if img.mode == "RGBA" else img.convert("RGBA")
    return rgba.rotate(deg, resample=Image.Resampling.BICUBIC, expand=True)


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
