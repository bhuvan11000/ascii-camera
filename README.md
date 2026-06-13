# ASCII Camera

A fullscreen terminal tool that renders your webcam feed as ASCII art in real time.

## Features

- Real-time conversion of camera frames to ASCII characters
- Fullscreen terminal display that fills every available row and column
- 70-character brightness ramp for high-fidelity luminance mapping
- 24-bit truecolor output using ANSI escape sequences (full RGB per character)
- Automatic scaling to match any terminal size on the fly
- Mirror mode (horizontal flip) so it behaves like a natural viewfinder
- Adjustable contrast, invertable brightness, and togglable color
- Live FPS counter and interactive status bar

## Requirements

- Python 3.8 or later
- A webcam accessible via Video4Linux (`/dev/video*`) or equivalent
- A terminal emulator with truecolor support for color mode (most modern terminals qualify: kitty, alacritty, wezterm, iTerm2, GNOME Terminal, Windows Terminal, etc.)

## Installation

Clone the repository and install the dependencies into a virtual environment:

```bash
git clone <repo-url> && cd ascii-camera
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

### Command-line options

| Flag              | Description                          | Default |
|-------------------|--------------------------------------|---------|
| `--device N`      | Camera device index                  | `0`     |
| `--color`         | Start with truecolor mode enabled    | off     |
| `--invert`        | Start with inverted brightness       | off     |
| `--contrast F`    | Initial contrast multiplier          | `1.0`   |

Examples:

```bash
# Use the second camera, start in color mode
python main.py --device 1 --color

# High contrast, inverted
python main.py --contrast 2.0 --invert
```

### Keyboard controls

All controls work while the viewer is running:

| Key            | Action                            |
|----------------|-----------------------------------|
| `q` / `Esc`    | Quit                              |
| `c`            | Toggle truecolor mode             |
| `i`            | Invert brightness mapping         |
| `+` / `=`      | Increase contrast (step of 0.2)   |
| `-` / `_`      | Decrease contrast (step of 0.2)   |
| `r`            | Reset all settings to defaults    |
| `h`            | Toggle the help/status bar        |

## How it works

1. **Capture** -- OpenCV grabs a frame from the webcam and mirrors it horizontally.
2. **Resize** -- The frame is scaled down to match the terminal's character grid (columns x rows). Terminal characters are roughly twice as tall as they are wide, so the vertical axis is compressed accordingly.
3. **Grayscale + contrast** -- The frame is converted to grayscale and an optional contrast curve is applied.
4. **ASCII mapping** -- Each pixel's brightness (0--255) is mapped to one of 70 characters ordered from dark to bright:
   ```
    .'`^",:;Il!i><~+_-?][}{1)(|\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$
   ```
5. **Render** -- In monochrome mode, lines are written via curses. In color mode, each character is wrapped in an ANSI 24-bit color escape sequence (`ESC[38;2;R;G;Bm`) derived from the original pixel's RGB value, and written directly to stdout.

## Project structure

```
ascii-camera/
  main.py              -- entry point and main loop
  ascii_converter.py   -- frame-to-ASCII conversion pipeline
  camera.py            -- OpenCV camera wrapper
  renderer.py          -- curses + truecolor terminal renderer
  requirements.txt     -- Python dependencies
```

## Troubleshooting

**"Could not open camera"**
- Make sure no other application is using the camera.
- Try a different device index: `python main.py --device 1`.
- On Linux, verify the device exists: `ls /dev/video*`.

**Color mode looks wrong or garbled**
- Your terminal may not support 24-bit truecolor. Run `echo -e "\033[38;2;255;0;0mRED\033[0m"` -- if it prints "RED" in red, your terminal is fine.
- Some multiplexers (older tmux, screen) strip truecolor sequences. Use `tmux -2` or set `set -g default-terminal "tmux-256color"`.

**Low FPS**
- Resize your terminal smaller. Fewer characters means less work per frame.
- Color mode is slower than monochrome because it emits per-character escape sequences.
- Close other applications that may be consuming CPU.
