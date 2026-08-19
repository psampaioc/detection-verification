# YOLO Detection Verification

Small Python CLI that converts a YOLO image/label dataset into a review video.
It reads every image, draws YOLO bounding boxes directly into that image, and
streams the annotated frames to `bounding_boxes.mp4`.

## Important: conversion is destructive

The program overwrites image pixels in `images/`. It does not move or copy
images to another folder. Keep the original dataset on the NAS or make a
backup before running it.

Labels and image files are matched by their complete filename stem. Empty
labels produce video frames without boxes; every image is still included.

## Requirements

- Python 3.9 or newer;
- Pillow;
- `ffmpeg` available in `PATH`.

The Python CLI is intended for Linux, macOS, and Windows, provided Python,
Pillow, and ffmpeg are installed.

## Installation

From this repository directory:

```bash
python -m pip install .
```

If the operating system rejects global installation, use a virtual environment:

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
python -m pip install .
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install .
```

The install creates the command `detection-verification`.

## Dataset layout

To process one split, the current directory must contain:

```text
split/
├── images/
└── labels/
```

To process all splits, the current directory must contain:

```text
dataset/
├── train/images/
├── train/labels/
├── valid/images/
├── valid/labels/
├── test/images/
└── test/labels/
```

The names `train`, `valid`, and `test` are the split names supported by
`--all`.

## Commands and flags

### `--video`

Required conversion flag. Processes the current split, draws boxes in place,
and creates `bounding_boxes.mp4`.

```bash
cd /path/to/dataset/train
detection-verification --video
```

This modifies only `train/images/` and creates `train/bounding_boxes.mp4`.

### `--all`

Processes `train`, `valid`, and `test` below the current directory. It must be
combined with `--video`:

```bash
cd /path/to/dataset
detection-verification --all --video
```

It creates one video per split and modifies the images in all three splits.

### Optional positional `dataset_dir`

The input directory is optional and defaults to the current directory (`.`).
Normally, do not provide it:

```bash
cd /path/to/dataset/train
detection-verification --video
```

It can be supplied when needed:

```bash
detection-verification /path/to/dataset/train --video
```

### Complete command reference

```text
detection-verification [dataset_dir] [--video] [--all]
```

Valid examples:

```bash
detection-verification --video
detection-verification --all --video
detection-verification /path/to/train --video
detection-verification /path/to/dataset --all --video
```

There is no `--move`, `--copy`, `--fps`, or `--overwrite` flag. The program
always uses 10 FPS, overwrites `bounding_boxes.mp4`, and modifies images in
place.

## Output and diagnostics

For each processed split it prints:

- number of images scanned;
- number of images with at least one box;
- number of images without boxes;
- number of missing label files.

Malformed YOLO labels, missing folders, unsupported dimensions, missing ffmpeg,
and encoder failures stop the command with an error.

## Without installing

From the repository directory, run the Python file directly:

```bash
python detection_verification.py --video
python detection_verification.py --all --video
```

The optional `detection_verification.sh` launcher is POSIX-only; Windows users
should use the Python commands.
