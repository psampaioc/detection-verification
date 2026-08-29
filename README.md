# YOLO Detection Verification

An interactive command-line tool for visually reviewing YOLO object-detection
annotations. It reads one dataset split, reports its contents, draws the
annotated bounding boxes directly into the existing images, and creates a
complete MP4 review video containing every frame.

## Quick start

Install once:

```bash
uv tool install git+https://github.com/psampaioc/detection-verification.git
```

Go to a split containing `images/` and `labels/`, then run:

```bash
cd /path/to/dataset/train
detection-verification
```

The tool prints the dataset counts and asks for confirmation:

```text
Images: 1021
Labels: 1021
Frames com detection: 474
Gerar video a 15 FPS? (y/n ou y -fps N):
```

Respond with one of these exact forms:

| Input | Result |
| --- | --- |
| `y` | Draw boxes in place and create `video.mp4` at 15 FPS. |
| `y -fps 30` | Draw boxes in place and create `video.mp4` at 30 FPS. |
| `n` or anything else | Cancel without modifying the dataset. |

There are no command-line flags or path arguments. The current directory is
always the input directory.

## What it expects

The current directory must contain one split in this form:

```text
split/
├── images/
│   ├── image_001.jpg
│   └── image_002.jpg
└── labels/
    ├── image_001.txt
    └── image_002.txt
```

Each label file uses the standard YOLO format:

```text
class_id center_x center_y width height
```

Coordinates are normalized from 0 to 1. An empty label file represents a
frame without a detection; that frame is still included in the video.

The input should contain frames from one continuous source sequence when the
output is intended to represent a continuous video. Repeated frame numbers
from different source videos cannot be reconstructed reliably from filenames.

## Output and data safety

After confirmation, the tool:

- overwrites images in `images/` with the red bounding boxes drawn;
- creates or replaces `video.mp4` beside `images/` and `labels/`;
- includes both frames with detections and frames without detections;
- does not copy or move the dataset.

This is intentionally destructive. Keep an unmodified backup before using
`y`. The program validates folders, labels, matching names, dimensions, and
`ffmpeg` before starting the conversion, but a backup is still the recovery
mechanism for overwritten image pixels.

## Installation options

### Option A — `uv` (recommended)

`uv` installs the CLI in an isolated Python environment and exposes its
console command globally. It is the simplest option for normal use:

```bash
uv tool install git+https://github.com/psampaioc/detection-verification.git
```

Update to the latest repository version:

```bash
uv tool install --reinstall git+https://github.com/psampaioc/detection-verification.git
```

Verify that the command is visible to the shell:

```bash
command -v detection-verification
detection-verification
```

If the command is not found, make sure `uv`'s executable directory is in
`PATH` and open a new terminal. On Linux and macOS this is commonly:

```text
~/.local/bin
```

### Option B — `pipx`

`pipx` is another suitable Python application installer. It also creates an
isolated environment and exposes the CLI globally:

```bash
pipx install git+https://github.com/psampaioc/detection-verification.git
```

Update it with:

```bash
pipx upgrade detection-verification
```

Use either `uv` or `pipx`; installing with both is unnecessary.

### Option C — local development with `pip`

Use a virtual environment when developing or modifying this repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

The command is then available while that environment is active. This method
is not the preferred way to install a standalone global CLI. Avoid forcing a
system Python installation with `--break-system-packages`; that bypasses the
operating system's package protection and can create conflicts with system
tools.

### Why not `npx`?

`npx` is the package runner for Node.js packages. This project is a Python
package, so `npx` is not an installation method for it. The equivalent Python
application tools are `uv tool` and `pipx`.

## System dependency: `ffmpeg`

Pillow is installed automatically by `uv`, `pipx`, or `pip`. The MP4 encoder
must be installed separately and available as `ffmpeg` in `PATH`.

Ubuntu/Debian:

```bash
sudo apt update
sudo apt install ffmpeg
```

macOS with Homebrew:

```bash
brew install ffmpeg
```

Windows with `winget`:

```powershell
winget install Gyan.FFmpeg.Shared
```

Confirm it with:

```bash
ffmpeg -version
```

## Troubleshooting

`Missing required folder(s)` means the command was not run inside a directory
containing both `images/` and `labels/`.

`No supported images found` means the `images/` directory is empty or uses an
unsupported extension. Supported extensions are `.jpg`, `.jpeg`, `.png`,
`.bmp`, and `.webp`.

`label file(s) have no matching image` means a `.txt` label does not have an
image with the same complete filename stem.

`ffmpeg is required` means the encoder is missing or is not available in the
current shell `PATH`.

## Development and release process

This section documents how the tool was built and how future changes should
be validated.

### 1. Keep the application small

The runtime consists of one Python module, Pillow, and the system `ffmpeg`.
Pillow handles image decoding, YOLO coordinate conversion, and box drawing.
`ffmpeg` receives raw RGB frames through standard input and encodes the final
MP4. No machine-learning model is loaded by this review tool.

### 2. Inspect before writing

The program resolves the current working directory and checks for `images/`
and `labels/`. It enumerates supported images and `.txt` files, matches them
by their complete filename stem, parses every label, and checks all image
dimensions before asking for confirmation. Invalid data fails before image
pixels can be overwritten.

### 3. Count and confirm

`Labels` is the number of label files. `Frames com detection` counts images
whose matching label contains at least one valid YOLO row. Empty labels are
valid negative frames and are not discarded.

Only `y` or `y -fps N` starts the destructive operation. Any other response
returns without creating output or changing images.

### 4. Convert as a stream

Images are processed in deterministic filename order, one at a time. For each
image, the normalized YOLO coordinates are converted to pixel coordinates,
red rectangles and class labels are drawn, the image is overwritten in place,
and its RGB pixels are sent immediately to `ffmpeg`. Memory usage therefore
stays close to one image plus its current annotation.

Every image is sent to the encoder, whether its label is empty or populated.
The output frame rate is 15 FPS by default or the positive integer supplied in
the interactive `y -fps N` form.

### 5. Package as a global CLI

The `pyproject.toml` declares the Python dependency and this console entry
point:

```toml
[project.scripts]
detection-verification = "detection_verification:main"
```

`uv tool install` builds the package in an isolated environment and places a
launcher on the user's `PATH`. The user can therefore run the command from
any directory without activating a repository virtual environment.

### 6. Validate changes

Before committing a change:

```bash
python3 -m py_compile detection_verification.py
uv build
```

Also test the important behavior in a temporary dataset:

- missing folders fail clearly;
- `n` leaves images and output unchanged;
- `y` creates a 15 FPS video;
- `y -fps 30` creates a 30 FPS video;
- the video frame count equals the image count;
- positive and empty labels produce boxed and unboxed frames respectively.

Run repository hygiene checks before publication. Do not commit datasets,
images, videos, virtual environments, build outputs, caches, credentials, or
machine-specific paths.
