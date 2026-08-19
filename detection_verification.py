#!/usr/bin/env python3
"""Convert a YOLO image/label split into in-place annotated images and MP4."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError as exc:  # pragma: no cover - exercised by the CLI
    raise SystemExit("Missing dependency: install Pillow with: python3 -m pip install Pillow") from exc


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_FPS = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find non-empty YOLO labels and create images with bounding boxes."
    )
    parser.add_argument(
        "dataset_dir",
        type=Path,
        nargs="?",
        default=Path("."),
        help="Optional input directory (default: current directory).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process train, valid and test below the current/input directory.",
    )
    parser.add_argument(
        "--video",
        action="store_true",
        help="Draw boxes into images in place and create bounding_boxes.mp4.",
    )
    return parser.parse_args()


def validate_split(split_dir: Path) -> tuple[Path, Path]:
    images_dir = split_dir / "images"
    labels_dir = split_dir / "labels"
    missing = [str(path) for path in (images_dir, labels_dir) if not path.is_dir()]
    if missing:
        raise ValueError(f"Expected images/ and labels/ inside {split_dir}; missing: {', '.join(missing)}")
    return images_dir, labels_dir


def read_boxes(label_path: Path) -> list[tuple[int, float, float, float, float]]:
    boxes = []
    for line_number, raw_line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        fields = raw_line.split()
        if len(fields) != 5:
            raise ValueError(f"{label_path}:{line_number}: expected 5 YOLO fields, got {len(fields)}")
        try:
            class_id = int(fields[0])
            values = tuple(float(value) for value in fields[1:])
        except ValueError as exc:
            raise ValueError(f"{label_path}:{line_number}: non-numeric YOLO value") from exc
        if class_id < 0 or not all(0.0 <= value <= 1.0 for value in values):
            raise ValueError(f"{label_path}:{line_number}: coordinates must be in [0, 1]")
        _, _, width, height = values
        if width <= 0 or height <= 0:
            raise ValueError(f"{label_path}:{line_number}: width and height must be positive")
        boxes.append((class_id, *values))
    return boxes


def annotated_image(image_path: Path, boxes: list[tuple[int, float, float, float, float]]) -> Image.Image:
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    image_width, image_height = image.size
    for class_id, center_x, center_y, width, height in boxes:
        x1 = (center_x - width / 2) * image_width
        y1 = (center_y - height / 2) * image_height
        x2 = (center_x + width / 2) * image_width
        y2 = (center_y + height / 2) * image_height
        draw.rectangle((x1, y1, x2, y2), outline=(255, 0, 0), width=max(2, image_width // 320))
        draw.text((max(0, x1), max(0, y1 - 14)), f"class {class_id}", fill=(255, 0, 0))
    return image


def natural_image_sort_key(path: Path) -> tuple[object, ...]:
    return tuple(int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name))


def process_video_split(split_dir: Path) -> dict[str, int]:
    images_dir, labels_dir = validate_split(split_dir)
    image_paths = sorted(
        [path for path in images_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS],
        key=natural_image_sort_key,
    )
    if not image_paths:
        raise ValueError(f"No supported images found in {images_dir}")

    output_path = split_dir / "bounding_boxes.mp4"
    first_image = Image.open(image_paths[0]).convert("RGB")
    width, height = first_image.size
    first_image.close()
    if width % 2 or height % 2:
        raise ValueError(f"Video requires even dimensions, got {width}x{height}")

    command = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}", "-r", str(VIDEO_FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_path),
    ]
    try:
        encoder = subprocess.Popen(command, stdin=subprocess.PIPE)
    except FileNotFoundError as exc:
        raise ValueError("ffmpeg is required for --video but was not found in PATH") from exc

    stats = {"images_scanned": 0, "images_annotated": 0, "images_without_boxes": 0, "missing_labels": 0}
    try:
        for image_path in image_paths:
            stats["images_scanned"] += 1
            label_path = labels_dir / f"{image_path.stem}.txt"
            if not label_path.is_file():
                stats["missing_labels"] += 1
                boxes = []
            else:
                boxes = read_boxes(label_path) if label_path.read_text(encoding="utf-8").strip() else []
            if boxes:
                stats["images_annotated"] += 1
            else:
                stats["images_without_boxes"] += 1
            image = annotated_image(image_path, boxes)
            image.save(image_path)
            encoder.stdin.write(image.tobytes())
            image.close()
        encoder.stdin.close()
        return_code = encoder.wait()
        if return_code != 0:
            raise ValueError(f"ffmpeg failed with exit code {return_code}")
    except Exception:
        if encoder.stdin and not encoder.stdin.closed:
            encoder.stdin.close()
        encoder.kill()
        encoder.wait()
        raise
    return stats


def main() -> int:
    args = parse_args()
    root = args.dataset_dir.resolve()
    if args.all:
        split_dirs = [root / name for name in ("train", "valid", "test") if (root / name).is_dir()]
        if not split_dirs:
            print(f"ERROR: no train/valid/test directories found below {root}", file=sys.stderr)
            return 2
    else:
        split_dirs = [root]

    if args.video:
        for split_dir in split_dirs:
            try:
                stats = process_video_split(split_dir)
            except (ValueError, OSError) as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                return 2
            print(f"{split_dir / 'bounding_boxes.mp4'}: {stats}")
        return 0
    print("Use --video to create the bounding-box review video.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
