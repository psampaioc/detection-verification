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

## Portable installation

The Python CLI is the portable interface and works on Linux, macOS, and
Windows. From this repository directory, install it with:

```bash
python -m pip install .
```

Then, from inside a split directory such as `train/`, `valid/`, or `test/`,
process only the current directory:

```bash
detection-verification
```

From the dataset root, process all available splits with `--all`:

```bash
detection-verification --all
```

Without installing, the same commands work from this repository directory:

```bash
python detection_verification.py
python detection_verification.py --all
```

The optional `detection_verification.sh` launcher is only for POSIX shells;
Windows users should use the Python commands above.

Only after checking the generated review output, intentionally move positive
source files to reclaim space:

```bash
detection-verification --all --move
```

Moving files makes the original YOLO dataset incomplete. Keep a backup or use
the default non-destructive mode if the dataset may still be needed for model
training.
