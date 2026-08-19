# Technical specification

## Goal

Create a fast local review video for YOLO object-detection datasets without
loading a machine-learning model. The tool makes annotations visible by
drawing each bounding box directly into its corresponding image.

## Architecture

One Python CLI, Pillow for image I/O and drawing, and the system `ffmpeg`
executable for MP4 encoding. Processing is streaming: one image is handled at
a time, so memory usage is approximately one image plus the current annotation.

## Algorithm

1. Detect whether the current directory is a split or contains `train`, `valid`,
   and `test` splits when `--all` is present.
2. Validate that each split has `images/` and `labels/`.
3. Enumerate every supported image in deterministic natural filename order.
4. Match each image to its label using the complete filename stem.
5. Parse YOLO rows: `class center_x center_y width height`.
6. Validate class and normalized coordinates.
7. Convert normalized coordinates to pixels and draw red rectangles and class text.
8. Overwrite the image in place.
9. Stream the annotated frame to `ffmpeg` and write `bounding_boxes.mp4`.

## Non-goals

- No model inference or automatic judgment that a box contains a person.
- No regex-based matching by `frame_00004`; names can repeat across sources.
- No model inference or automatic judgment that a box contains a person.
- No preservation of local image pixels; the NAS backup is the recovery source.
- No dataset files committed to the public repository.

## Acceptance criteria

- Every image is represented in the output video, including negative frames.
- Annotated images have visible boxes corresponding to their labels.
- Missing labels, malformed labels, inconsistent dimensions, and encoder errors
  are reported and produce a non-zero exit status.
