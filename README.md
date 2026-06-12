# ASCII Camera

A fullscreen terminal tool that previews your camera feed as real-time ASCII art.

## Features

- **Real-time ASCII rendering** — converts camera frames to ASCII characters at high FPS
- **Fullscreen terminal UI** — fills your entire terminal with ASCII art
- **Brightness-mapped characters** — uses a carefully ordered character ramp for accurate luminance
- **Adaptive sizing** — automatically scales to fit any terminal size
- **Color support** — optional ANSI color mode for terminals that support it
- **Keyboard controls** — toggle color, invert, adjust contrast, and more on the fly

## Requirements

- Python 3.8+
- A working webcam
- A terminal emulator (the bigger the better!)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

### Keyboard Controls

| Key       | Action                        |
|-----------|-------------------------------|
| `q` / `ESC` | Quit                       |
| `c`       | Toggle color mode             |
| `i`       | Invert brightness mapping     |
| `+` / `=` | Increase contrast             |
| `-`       | Decrease contrast             |
| `r`       | Reset settings to defaults    |
| `h`       | Toggle help overlay           |

## How It Works

1. Captures frames from your webcam via OpenCV
2. Resizes each frame to match the terminal dimensions
3. Converts pixel brightness to ASCII characters
4. Renders the full frame to the terminal using curses

## License

MIT
