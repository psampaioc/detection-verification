# Technical specification

## Goal

Create a fast local review set for YOLO object-detection datasets without
loading a machine-learning model. The tool must make the annotation visible by
drawing each bounding box on its corresponding image.

## Architecture

One Python CLI, standard-library orchestration, and Pillow for image I/O and
drawing. Processing is streaming: one label and one image are handled at a
time, so memory usage is approximately one image plus the current annotation.

## Algorithm

1. Validate that the input has `images/` and `labels/`.
2. Enumerate `labels/*.txt` once in sorted order.
3. Skip empty labels.
4. Match the image using the complete label stem and supported image extension.
5. Parse YOLO rows: `class center_x center_y width height`.
6. Validate class and normalized coordinates.
7. Convert normalized coordinates to pixels.
8. Draw red rectangles and class text.
9. Save the annotated image and copy the original label to the review output.
10. In `--move` mode, delete the source image and label only after both outputs
    have been written successfully.

## Non-goals

- No model inference or automatic judgment that a box contains a person.
- No regex-based matching by `frame_00004`; names can repeat across sources.
- No modification of original files in the default mode.
- No dataset files committed to the public repository.

## Acceptance criteria

- Positive labels are detected in all three splits.
- Every generated image has visible boxes corresponding to its label.
- Missing image pairs and malformed labels are reported and produce a non-zero
  exit status.
- A dry/default run leaves source checksums and file counts unchanged.
