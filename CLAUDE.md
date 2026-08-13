# Instructions for Claude Code

## UI visual validation

This is a desktop `customtkinter`/Tkinter app. This environment has no
screenshot/rendering tooling (no Pillow, no Ghostscript/ImageMagick) to
capture and inspect the Tkinter canvas.

Do not attempt to visually validate UI changes yourself and do not ask
whether visual validation is needed. Implement the change, verify it with
unit tests and by reasoning about the rendering code, then say so plainly.
The user runs the app locally (`.\run.bat`) to check the result and will
share screenshots if something needs fixing.
