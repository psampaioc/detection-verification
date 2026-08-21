#!/usr/bin/env python3
"""Draw YOLO annotations in place and create a complete review video."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError as exc:  # pragma: no cover - exercised by the CLI
    raise SystemExit("Missing dependency: install Pillow with: python3 -m pip install Pillow") from exc


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
DEFAULT_FPS = 15
FPS_REQUEST = re.compile(r"^[yY](?:\s+-fps\s+([1-9][0-9]*))?$")
Box = tuple[int, float, float, float, float]


def natural_image_sort_key(path: Path) -> tuple[object, ...]:
    """Sort names naturally while retaining the complete filename as a tie-breaker."""

    return tuple(int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name))


def read_boxes(label_path: Path) -> list[Box]:
    """Read and validate one YOLO label file."""

    boxes: list[Box] = []
    for line_number, raw_line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        fields = raw_line.split()
        if len(fields) != 5:
            raise ValueError(f"{label_path}:{line_number}: expected 5 YOLO fields, got {len(fields)}")
        try:
            class_id = int(fields[0])
            center_x, center_y, width, height = (float(value) for value in fields[1:])
        except ValueError as exc:
            raise ValueError(f"{label_path}:{line_number}: non-numeric YOLO value") from exc
        values = (center_x, center_y, width, height)
        if class_id < 0 or not all(0.0 <= value <= 1.0 for value in values):
            raise ValueError(f"{label_path}:{line_number}: coordinates must be in [0, 1]")
        if width <= 0 or height <= 0:
            raise ValueError(f"{label_path}:{line_number}: width and height must be positive")
        boxes.append((class_id, center_x, center_y, width, height))
    return boxes


def inspect_current_directory() -> tuple[Path, Path, list[Path], dict[str, list[Box]]]:
    """Validate the current directory and collect images and labels before writing anything."""

    root = Path.cwd()
    images_dir = root / "images"
    labels_dir = root / "labels"
    missing = [name for name, path in (("images/", images_dir), ("labels/", labels_dir)) if not path.is_dir()]
    if missing:
        raise ValueError(f"Missing required folder(s) in {root}: {', '.join(missing)}")

    image_paths = sorted(
        [path for path in images_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS],
        key=natural_image_sort_key,
    )
    label_paths = sorted(labels_dir.glob("*.txt"), key=natural_image_sort_key)
    if not image_paths:
        raise ValueError(f"No supported images found in {images_dir}")

    labels_by_stem: dict[str, list[Box]] = {}
    for label_path in label_paths:
        labels_by_stem[label_path.stem] = read_boxes(label_path)

    image_stems = {path.stem for path in image_paths}
    unmatched_labels = sorted(set(labels_by_stem) - image_stems)
    if unmatched_labels:
        raise ValueError(
            f"{len(unmatched_labels)} label file(s) have no matching image: "
            + ", ".join(unmatched_labels[:3])
            + (" ..." if len(unmatched_labels) > 3 else "")
        )

    return images_dir, labels_dir, image_paths, labels_by_stem


def request_video_settings() -> int | None:
    """Ask for the only supported operation and return the requested FPS."""

    try:
        answer = input(f"Gerar video a {DEFAULT_FPS} FPS? (y/n ou y -fps N): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("Operacao cancelada.")
        return None

    match = FPS_REQUEST.fullmatch(answer)
    if not match:
        print("Operacao cancelada. Para continuar, escreva y ou y -fps N.")
        return None
    return int(match.group(1) or DEFAULT_FPS)


def annotated_image(image_path: Path, boxes: list[Box]) -> Image.Image:
    """Return an RGB image with its YOLO boxes drawn."""

    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    image_width, image_height = image.size
    line_width = max(2, image_width // 320)
    for class_id, center_x, center_y, width, height in boxes:
        x1 = (center_x - width / 2) * image_width
        y1 = (center_y - height / 2) * image_height
        x2 = (center_x + width / 2) * image_width
        y2 = (center_y + height / 2) * image_height
        draw.rectangle((x1, y1, x2, y2), outline=(255, 0, 0), width=line_width)
        draw.text((max(0, x1), max(0, y1 - 14)), f"class {class_id}", fill=(255, 0, 0))
    return image


def create_video(
    images_dir: Path,
    image_paths: list[Path],
    labels_by_stem: dict[str, list[Box]],
    fps: int,
) -> dict[str, int]:
    """Overwrite images with annotations and stream every frame to video.mp4."""

    dimensions = set()
    for image_path in image_paths:
        with Image.open(image_path) as image:
            dimensions.add(image.size)
    if len(dimensions) != 1:
        raise ValueError(f"All images must have the same dimensions; found {sorted(dimensions)}")

    width, height = next(iter(dimensions))
    if width % 2 or height % 2:
        raise ValueError(f"Video requires even dimensions, got {width}x{height}")
    if shutil.which("ffmpeg") is None:
        raise ValueError("ffmpeg is required but was not found in PATH")

    output_path = images_dir.parent / "video.mp4"
    command = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}", "-r", str(fps), "-i", "-",
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_path),
    ]
    try:
        encoder = subprocess.Popen(command, stdin=subprocess.PIPE)
    except OSError as exc:
        raise ValueError(f"Could not start ffmpeg: {exc}") from exc

    stats = {"images_scanned": 0, "frames_with_detection": 0, "frames_without_detection": 0}
    try:
        for image_path in image_paths:
            boxes = labels_by_stem.get(image_path.stem, [])
            if boxes:
                stats["frames_with_detection"] += 1
            else:
                stats["frames_without_detection"] += 1
            image = annotated_image(image_path, boxes)
            image.save(image_path)
            assert encoder.stdin is not None
            encoder.stdin.write(image.tobytes())
            image.close()
            stats["images_scanned"] += 1
        assert encoder.stdin is not None
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
    if len(sys.argv) != 1:
        print("Este programa nao aceita flags nem caminhos. Execute detection-verification dentro de uma pasta com images/ e labels/.")
        return 2
    try:
        _, _, image_paths, labels_by_stem = inspect_current_directory()
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    label_count = len(labels_by_stem)
    frames_with_detection = sum(bool(labels_by_stem.get(path.stem)) for path in image_paths)
    print(f"Images: {len(image_paths)}")
    print(f"Labels: {label_count}")
    print(f"Frames com detection: {frames_with_detection}")

    fps = request_video_settings()
    if fps is None:
        return 0
    try:
        stats = create_video(Path.cwd() / "images", image_paths, labels_by_stem, fps)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"Video criado: {Path.cwd() / 'video.mp4'}")
    print(f"FPS: {fps}")
    print(f"Frames processados: {stats['images_scanned']}")
    print(f"Frames com detection: {stats['frames_with_detection']}")
    print(f"Frames sem detection: {stats['frames_without_detection']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
