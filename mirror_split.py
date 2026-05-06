from pathlib import Path

from PIL import Image

from mirror import mirror_pair

INPUT_PATH = Path("image.png")
LEFT_OUTPUT_PATH = Path("image_left.png")
RIGHT_OUTPUT_PATH = Path("image_right.png")


def main() -> None:
    img = Image.open(INPUT_PATH)
    left, right = mirror_pair(img)
    left.save(LEFT_OUTPUT_PATH)
    right.save(RIGHT_OUTPUT_PATH)


if __name__ == "__main__":
    main()
