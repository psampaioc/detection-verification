# Changelog

## 1.0.0 — 2026-08-29

- Replaced flag-based execution with one interactive `detection-verification`
  command that operates in the current directory.
- Added dataset counts before confirmation.
- Added `y` for 15 FPS and `y -fps N` for a custom positive FPS value.
- Added cancellation for `n` and invalid input without modifying images.
- Added preflight validation before destructive conversion.
- Changed the output filename to `video.mp4`.
- Kept every frame in the output video, including empty-label frames.
- Removed the obsolete shell launcher.
- Expanded installation, troubleshooting, architecture, and release guidance.
