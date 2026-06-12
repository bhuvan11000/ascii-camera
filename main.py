#!/usr/bin/env python3
"""
ASCII Camera — Real-time camera-to-ASCII-art terminal viewer.

Usage:
    python main.py [--device N] [--color] [--invert]

Controls:
    q / ESC   Quit
    c         Toggle color
    i         Toggle invert
    + / =     Increase contrast
    - / _     Decrease contrast
    r         Reset to defaults
    h         Toggle help bar
"""

import argparse
import curses
import sys
import time

from ascii_converter import frame_to_ascii, frame_to_colored_ascii
from camera import Camera
from renderer import Renderer


# Default settings
DEFAULTS = {
    "contrast": 1.0,
    "inverted": False,
    "color": False,
    "show_help": True,
}

# Contrast bounds
CONTRAST_MIN = 0.2
CONTRAST_MAX = 5.0
CONTRAST_STEP = 0.2


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Real-time ASCII camera viewer for the terminal."
    )
    parser.add_argument(
        "--device",
        type=int,
        default=0,
        help="Camera device index (default: 0)",
    )
    parser.add_argument(
        "--color",
        action="store_true",
        help="Start with color mode enabled",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        help="Start with inverted brightness",
    )
    parser.add_argument(
        "--contrast",
        type=float,
        default=1.0,
        help="Initial contrast level (default: 1.0)",
    )
    return parser.parse_args()


def main_loop(stdscr, args):
    """Main application loop inside curses."""
    renderer = Renderer()
    renderer.init(stdscr)

    # State
    contrast = args.contrast
    inverted = args.invert
    color_on = args.color
    show_help = DEFAULTS["show_help"]

    cam = Camera(device=args.device)
    if not cam.open():
        renderer.show_error("ERROR: Could not open camera. Press any key to exit.")
        stdscr.nodelay(False)
        stdscr.getch()
        return

    try:
        while True:
            # --- Handle input ---
            key = renderer.get_key()

            if key in (ord('q'), ord('Q'), 27):  # q, Q, ESC
                break
            elif key in (ord('c'), ord('C')):
                color_on = not color_on
            elif key in (ord('i'), ord('I')):
                inverted = not inverted
            elif key in (ord('+'), ord('=')):
                contrast = min(CONTRAST_MAX, contrast + CONTRAST_STEP)
            elif key in (ord('-'), ord('_')):
                contrast = max(CONTRAST_MIN, contrast - CONTRAST_STEP)
            elif key in (ord('r'), ord('R')):
                contrast = DEFAULTS["contrast"]
                inverted = DEFAULTS["inverted"]
                color_on = DEFAULTS["color"]
            elif key in (ord('h'), ord('H')):
                show_help = not show_help

            # --- Capture frame ---
            frame = cam.read_frame()
            if frame is None:
                renderer.show_error("Camera read failed. Retrying...")
                time.sleep(0.1)
                continue

            # --- Convert to ASCII ---
            width, height = renderer.get_size()
            if width < 2 or height < 2:
                time.sleep(0.05)
                continue

            color_frame = None
            if color_on:
                lines, color_frame = frame_to_colored_ascii(
                    frame, width, height,
                    contrast=contrast, invert=inverted,
                )
            else:
                lines = frame_to_ascii(
                    frame, width, height,
                    contrast=contrast, invert=inverted,
                )

            # --- Render ---
            fps = renderer.update_fps()
            renderer.render_frame(lines, color_frame=color_frame, use_color=color_on)
            renderer.render_status_bar(fps, contrast, inverted, color_on, show_help)
            renderer.refresh()

    finally:
        cam.close()


def run():
    """Entry point: parse args and launch curses."""
    args = parse_args()

    try:
        curses.wrapper(lambda stdscr: main_loop(stdscr, args))
    except KeyboardInterrupt:
        pass
    finally:
        print("ASCII Camera closed. Goodbye!")


if __name__ == "__main__":
    run()
