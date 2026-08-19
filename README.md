# YOLO Detection Verification

Small, dependency-light utility for reviewing YOLO object-detection annotations.
It scans `labels/*.txt`, finds non-empty annotations, matches each label to the
image with the exact same filename stem, and writes an annotated review image
with red bounding boxes.

## Specification

- Input: one directory containing `images/` and `labels/`, or a dataset root with
  `train/`, `valid/`, and `test/` directories.
- Labels with no rows produce frames without boxes.
- Pairing: exact full stem match; no regex or shortened frame-number matching.
- Output: annotated images are written in place and `bounding_boxes.mp4` is
  written in the processed split.
- `--video` reads every image and label, draws boxes directly into the original
  image, and includes frames without boxes in the video.
- Exit status: non-zero if a positive label has no matching image or has an
  invalid YOLO line.

## Usage

## Portable installation

The Python CLI is the portable interface and works on Linux, macOS, and
Windows. From this repository directory, install it with:

```bash
python -m pip install .
```

The optional `detection_verification.sh` launcher is only for POSIX shells;
Windows users should use the Python commands above.

Create a full review video from the current split:

```bash
detection-verification --video
```

From the dataset root, create one video for each split:

```bash
detection-verification --all --video
```

This conversion overwrites the images in place and overwrites
`bounding_boxes.mp4`. Keep the NAS backup if the unmodified images may be
needed later.

The conversion is intentionally destructive to the local image pixels. Keep
the NAS backup if the unmodified images may be needed later.
