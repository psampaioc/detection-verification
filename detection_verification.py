#!/usr/bin/env python3
"""Create YOLO positive-image review sets with drawn bounding boxes.

The default mode is non-destructive: it writes annotated images and copies
positive labels to an output directory. Use --move only when intentionally
removing positive files from the source dataset.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError as exc:  # pragma: no cover - exercised by the CLI
    raise SystemExit("Missing dependency: install Pillow with: python3 -m pip install Pillow") from exc


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find non-empty YOLO labels and create images with bounding boxes."
    )
    parser.add_argument(
        "dataset_dir",
        type=Path,
        help="Directory containing images/ and labels/, or a dataset root with train/valid/test.",
    )
    parser.add_argument(
        "--all-splits",
        action="store_true",
        help="Process train, valid and test below dataset_dir.",
    )
    parser.add_argument(
        "--output-name",
        default=".",
        help="Output directory name inside each processed split (default: current split directory).",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Move positive labels and source images after annotated output is written. Destructive.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files.",
    )
    return parser.parse_args()


def validate_split(split_dir: Path) -> tuple[Path, Path]:
    images_dir = split_dir / "images"
    labels_dir = split_dir / "labels"
    missing = [str(path) for path in (images_dir, labels_dir) if not path.is_dir()]
    if missing:
        raise ValueError(f"Expected images/ and labels/ inside {split_dir}; missing: {', '.join(missing)}")
    return images_dir, labels_dir


def find_image(images_dir: Path, label_path: Path) -> Path | None:
    for extension in IMAGE_EXTENSIONS:
        candidate = images_dir / f"{label_path.stem}{extension}"
        if candidate.is_file():
            return candidate
    return None


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


def process_split(split_dir: Path, output_name: str, move: bool, overwrite: bool) -> dict[str, int]:
    images_dir, labels_dir = validate_split(split_dir)
    output_dir = split_dir / output_name
    positive_labels_dir = output_dir / "positive_labels"
    positive_images_dir = output_dir / "positive_images"
    positive_labels_dir.mkdir(parents=True, exist_ok=True)
    positive_images_dir.mkdir(parents=True, exist_ok=True)

    stats = {"labels_scanned": 0, "positive_labels": 0, "images_written": 0, "missing_images": 0, "errors": 0}
    for label_path in sorted(labels_dir.glob("*.txt")):
        stats["labels_scanned"] += 1
        if not label_path.read_text(encoding="utf-8").strip():
            continue
        stats["positive_labels"] += 1
        image_path = find_image(images_dir, label_path)
        if image_path is None:
            stats["missing_images"] += 1
            print(f"WARNING: no matching image for {label_path.name}", file=sys.stderr)
            continue
        try:
            boxes = read_boxes(label_path)
            output_label = positive_labels_dir / label_path.name
            output_image = positive_images_dir / image_path.name
            if not overwrite and (output_label.exists() or output_image.exists()):
                raise FileExistsError(f"output exists for {label_path.stem}; use --overwrite")
            annotated_image(image_path, boxes).save(output_image, quality=95)
            shutil.copy2(label_path, output_label)
            stats["images_written"] += 1
            if move:
                image_path.unlink()
                label_path.unlink()
        except (OSError, ValueError) as exc:
            stats["errors"] += 1
            print(f"ERROR: {exc}", file=sys.stderr)
    return stats


def main() -> int:
    args = parse_args()
    root = args.dataset_dir.resolve()
    if args.all_splits:
        split_dirs = [root / name for name in ("train", "valid", "test") if (root / name).is_dir()]
        if not split_dirs:
            print(f"ERROR: no train/valid/test directories found below {root}", file=sys.stderr)
            return 2
    else:
        split_dirs = [root]

    if args.move:
        print("WARNING: --move removes positive source files from the original dataset.")

    total = {key: 0 for key in ("labels_scanned", "positive_labels", "images_written", "missing_images", "errors")}
    for split_dir in split_dirs:
        try:
            stats = process_split(split_dir, args.output_name, args.move, args.overwrite)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(f"{split_dir}: {stats}")
        for key, value in stats.items():
            total[key] += value
    print(f"TOTAL: {total}")
    return 1 if total["missing_images"] or total["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
