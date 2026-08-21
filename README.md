# YOLO Detection Verification

Small interactive CLI for checking YOLO annotations visually. It scans the
current directory, reports the dataset counts, draws the labelled bounding
boxes directly into `images/`, and creates a complete MP4 containing every
frame, including frames without detections.

## Important: conversion is destructive

When confirmed, the tool overwrites the image pixels in `images/`. It does not
copy or move images. Keep an unmodified backup before generating the video.

## Requirements

- Python 3.9 or newer;
- `ffmpeg` available in `PATH`;
- Pillow (installed automatically with the application).

## Global installation

Install once with `uv`:

```bash
uv tool install git+https://github.com/psampaioc/detection-verification.git
```

This creates an isolated application environment and makes the command
`detection-verification` available from any directory. `uv` must have its
executable directory in `PATH`; normally this is `~/.local/bin`.

To update an existing installation:

```bash
uv tool install --reinstall git+https://github.com/psampaioc/detection-verification.git
```

Confirm the installation with:

```bash
command -v detection-verification
```

## Dataset layout

Run the command inside the split you want to review:

```text
train/
├── images/
└── labels/
```

The tool only uses the current directory. It does not search for or process
`train`, `valid`, or `test` automatically.

## Usage

```bash
cd /path/to/train
detection-verification
```

The program first prints:

```text
Images: <number>
Labels: <number>
Frames com detection: <number>
```

It then asks:

```text
Gerar video a 15 FPS? (y/n ou y -fps N):
```

Accepted responses:

- `y` — draw boxes in place and create `video.mp4` at 15 FPS;
- `y -fps 30` — do the same at 30 FPS, or any other positive integer FPS.

Any other response, including `n`, cancels without modifying images.

There are no command-line flags, positional paths, split selectors, copy
options, or move options.

## Processing behavior

1. Confirm that the current directory contains both `images/` and `labels/`.
2. Count supported images and YOLO label files.
3. Parse and validate all labels before changing any image.
4. Match each image to its label by the complete filename stem.
5. Sort image filenames deterministically.
6. Draw every corresponding box in red directly into the original image.
7. Stream every processed image to `video.mp4`, including images with empty
   labels.

The dataset should contain one continuous source sequence if the output is
intended to represent a continuous video. Repeated frame numbers from
different source sequences cannot be reliably reconstructed from filenames
alone.

## Diagnostics

The program stops before modifying images when it finds:

- missing `images/` or `labels/`;
- no supported images;
- malformed YOLO rows;
- invalid normalized coordinates;
- label files without matching images;
- inconsistent image dimensions;
- missing `ffmpeg`.

## Local development

From this repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

The package exposes the same `detection-verification` command inside the
environment. For normal use, prefer the global `uv tool install` method above.
