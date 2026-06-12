"""
Terminal renderer — fullscreen curses-based display for ASCII art.

Supports two color modes:
  - Truecolor (24-bit): uses raw ANSI escape sequences for full RGB per character.
    Works on most modern terminals (kitty, alacritty, wezterm, iTerm2, GNOME Terminal, etc.)
  - Monochrome: fast whole-line rendering via curses.
"""

import curses
import io
import sys
import time


class Renderer:
    """Fullscreen terminal renderer using curses + truecolor ANSI escapes."""

    def __init__(self):
        self._stdscr = None
        self._fps_history: list[float] = []
        self._last_frame_time: float = 0

    def init(self, stdscr):
        """Initialize the renderer with a curses screen."""
        self._stdscr = stdscr
        curses.curs_set(0)       # Hide cursor
        curses.start_color()
        curses.use_default_colors()
        stdscr.nodelay(True)     # Non-blocking getch
        stdscr.timeout(0)

        # One color pair for the status bar (white on default)
        curses.init_pair(1, curses.COLOR_WHITE, -1)

    def get_size(self) -> tuple[int, int]:
        """Get terminal size as (width, height) in characters.

        Reserves 1 row at the bottom for the status bar.
        """
        max_y, max_x = self._stdscr.getmaxyx()
        return max_x, max_y - 1

    def get_key(self) -> int:
        """Non-blocking key read. Returns -1 if no key pressed."""
        try:
            return self._stdscr.getch()
        except curses.error:
            return -1

    # ------------------------------------------------------------------ #
    #  Truecolor rendering (bypasses curses color pairs entirely)         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_truecolor_frame(
        lines: list[str],
        color_frame,
        max_x: int,
        max_y: int,
    ) -> str:
        """Build a single string with ANSI 24-bit color codes for every character.

        This writes directly to stdout, bypassing curses' internal buffer
        for the content area, which lets us use unlimited RGB colors.
        """
        buf = io.StringIO()
        reset = "\033[0m"

        for y, line in enumerate(lines):
            if y >= max_y:
                break
            # Move cursor to start of row
            buf.write(f"\033[{y + 1};1H")

            prev_r = prev_g = prev_b = -1
            chars_written = 0

            for x, ch in enumerate(line):
                if x >= max_x:
                    break
                b_val, g_val, r_val = int(color_frame[y, x, 0]), int(color_frame[y, x, 1]), int(color_frame[y, x, 2])

                # Only emit a new SGR sequence when the color actually changes
                if r_val != prev_r or g_val != prev_g or b_val != prev_b:
                    buf.write(f"\033[38;2;{r_val};{g_val};{b_val}m")
                    prev_r, prev_g, prev_b = r_val, g_val, b_val

                buf.write(ch)
                chars_written += 1

            # Clear rest of line
            if chars_written < max_x:
                buf.write("\033[K")

        buf.write(reset)
        return buf.getvalue()

    # ------------------------------------------------------------------ #
    #  Public render methods                                               #
    # ------------------------------------------------------------------ #

    def render_frame(self, lines: list[str], color_frame=None, use_color: bool = False):
        """Render ASCII lines to the terminal.

        Args:
            lines: List of ASCII strings to display.
            color_frame: Optional BGR numpy array for colored rendering.
            use_color: Whether to apply 24-bit truecolor.
        """
        stdscr = self._stdscr
        max_y, max_x = stdscr.getmaxyx()

        if use_color and color_frame is not None:
            # Truecolor path: write ANSI escapes directly to stdout
            frame_str = self._build_truecolor_frame(lines, color_frame, max_x - 1, max_y - 1)
            sys.stdout.write(frame_str)
            sys.stdout.flush()
        else:
            # Monochrome path: fast curses line-by-line
            try:
                stdscr.erase()
                for y, line in enumerate(lines):
                    if y >= max_y - 1:
                        break
                    truncated = line[:max_x - 1]
                    try:
                        stdscr.addstr(y, 0, truncated)
                    except curses.error:
                        pass
            except curses.error:
                pass

    def render_status_bar(
        self,
        fps: float,
        contrast: float,
        inverted: bool,
        color_on: bool,
        show_help: bool,
    ):
        """Render a status bar at the bottom of the screen."""
        stdscr = self._stdscr
        max_y, max_x = stdscr.getmaxyx()
        status_y = max_y - 1

        parts = [
            f" FPS: {fps:4.1f}",
            f"Contrast: {contrast:.1f}",
            f"Inv: {'ON' if inverted else 'OFF'}",
            f"Color: {'ON' if color_on else 'OFF'}",
        ]
        if show_help:
            parts.append("[h]elp [q]uit [c]olor [i]nvert [+/-]contrast [r]eset")
        else:
            parts.append("[h] help")

        status = " │ ".join(parts)
        status = status[:max_x - 1]

        try:
            # When in truecolor mode we wrote directly to stdout,
            # so render the status bar via raw ANSI too for consistency.
            bar = f"\033[0m\033[{status_y + 1};1H\033[7m{status.ljust(max_x - 1)}\033[0m"
            sys.stdout.write(bar)
            sys.stdout.flush()

            # Also update curses so it stays in sync for monochrome frames
            stdscr.move(status_y, 0)
            stdscr.clrtoeol()
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(status_y, 0, status.ljust(max_x - 1))
            stdscr.attroff(curses.A_REVERSE)
        except curses.error:
            pass

    def refresh(self):
        """Push the frame to the terminal."""
        self._stdscr.noutrefresh()
        curses.doupdate()

    def update_fps(self) -> float:
        """Track and return the current FPS."""
        now = time.time()
        if self._last_frame_time > 0:
            dt = now - self._last_frame_time
            if dt > 0:
                self._fps_history.append(1.0 / dt)
                # Keep last 30 samples
                if len(self._fps_history) > 30:
                    self._fps_history.pop(0)
        self._last_frame_time = now
        return sum(self._fps_history) / len(self._fps_history) if self._fps_history else 0.0

    def show_error(self, message: str):
        """Display an error message centered on screen."""
        stdscr = self._stdscr
        max_y, max_x = stdscr.getmaxyx()
        try:
            stdscr.erase()
            cy, cx = max_y // 2, max(0, (max_x - len(message)) // 2)
            stdscr.addstr(cy, cx, message, curses.A_BOLD)
            stdscr.refresh()
        except curses.error:
            pass
