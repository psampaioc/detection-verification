# Technical specification

## Goal

Provide one portable interactive CLI command for visually reviewing YOLO
annotations in the current dataset split. The tool modifies images in place
and creates a complete review video without creating a second image dataset.

## CLI contract

```text
detection-verification
```

The command accepts no flags and no paths. It operates only in the current
working directory, which must contain `images/` and `labels/`.

The interactive input is the only operation selector:

- `y` creates `video.mp4` at 15 FPS;
- `y -fps N` creates `video.mp4` at positive integer rate `N`;
- every other input cancels without writing images or video.

## Architecture

One Python module, Pillow for image I/O and drawing, and the system `ffmpeg`
executable for MP4 encoding. `uv tool install` provides an isolated Python
environment and exposes the console entry point globally.

Processing is streaming: one annotated image is held in memory while its RGB
pixels are sent to ffmpeg. The dataset is not copied.

## Algorithm

1. Verify `images/` and `labels/` exist in the current directory.
2. Enumerate supported image files and `.txt` label files.
3. Parse and validate every label before modifying any image.
4. Report image count, label count, and `Frames com detection`.
5. Ask for `y`, `y -fps N`, or cancellation.
6. Match each image to its label by the complete filename stem.
7. Sort images deterministically by their complete filenames.
8. Convert YOLO normalized coordinates to pixels and draw red rectangles.
9. Overwrite each image in `images/`.
10. Stream every annotated image, including empty-label frames, to `video.mp4`.

## Safety and validation

The tool validates labels, matching label/image stems, image dimensions, and
ffmpeg availability before starting the destructive conversion. A source
backup remains the recovery mechanism because image pixels are intentionally
overwritten after confirmation.

The tool cannot reconstruct chronology when a dataset mixes multiple source
sequences that reuse frame numbers. The input dataset must therefore represent
one sequence if the output is intended to be a continuous video.

## Non-goals

- no model inference;
- no automatic semantic judgement of annotation quality;
- no copying, moving, or positive-only output folders;
- no processing of sibling `train`, `valid`, or `test` directories;
- no command-line flags or path arguments;
- no preservation of original image pixels inside the dataset directory.

## Acceptance criteria

- `detection-verification` works from any directory after global installation;
- missing folders produce a clear error and non-zero exit status;
- counts are printed before confirmation;
- `n` and invalid input leave the dataset unchanged;
- `y` produces a 15 FPS `video.mp4` by default;
- `y -fps 30` produces a 30 FPS `video.mp4`;
- every image is represented in the video;
- images with non-empty labels show their corresponding boxes;
- malformed labels, unmatched labels, inconsistent dimensions, missing ffmpeg,
  and encoder failures produce clear errors.
