# YOLO Detection Verification

Small, dependency-light utility for reviewing YOLO object-detection annotations.
It scans `labels/*.txt`, finds non-empty annotations, matches each label to the
image with the exact same filename stem, and writes an annotated review image
with red bounding boxes.

## Specification

- Input: one directory containing `images/` and `labels/`, or a dataset root with
  `train/`, `valid/`, and `test/` directories.
- Positive label: a `.txt` file containing at least one non-empty line.
- Pairing: exact full stem match; no regex or shortened frame-number matching.
- Output: `<split>/positive_labels/` and `<split>/positive_images/` by default.
- Safety: default mode preserves the original dataset. `--move` is an explicit
  destructive mode and removes positive source files only after the annotated
  image and label output succeed.
- Exit status: non-zero if a positive label has no matching image or has an
  invalid YOLO line.

## Usage

Install the only dependency:

```bash
python3 -m pip install Pillow
```

Process one split without changing the source:

```bash
python3 detection_verification.py /path/to/train
```

Process all available splits without changing the source:

```bash
python3 detection_verification.py /path/to/Person_Detection.v2i.yolov8 --all-splits
```

When launched from inside the dataset root, the dataset path can be omitted:

```bash
cd /path/to/Person_Detection.v2i.yolov8
python3 /path/to/detection_verification.py --all-splits
```

Only after checking the generated review output, intentionally move positive
source files to reclaim space:

```bash
python3 detection_verification.py /path/to/Person_Detection.v2i.yolov8 --all-splits --move
```

Moving files makes the original YOLO dataset incomplete. Keep a backup or use
the default non-destructive mode if the dataset may still be needed for model
training.
