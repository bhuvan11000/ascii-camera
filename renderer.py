"""
Terminal renderer — fullscreen curses-based display for ASCII art.
"""

import curses
import time


# Map rough BGR ranges to curses color pair indices
def _init_colors():
    """Initialize curses color pairs for colored ASCII output."""
    curses.start_color()
    curses.use_default_colors()

    # Define color pairs: pair_id -> (fg, bg)
    # We'll create pairs for the basic 8 ANSI colors
    color_map = {}
    pair_id = 1
    for color in [
        curses.COLOR_RED,
        curses.COLOR_GREEN,
        curses.COLOR_BLUE,
        curses.COLOR_YELLOW,
        curses.COLOR_CYAN,
        curses.COLOR_MAGENTA,
        curses.COLOR_WHITE,
    ]:
        curses.init_pair(pair_id, color, -1)
        color_map[color] = pair_id
        pair_id += 1

    return color_map


def bgr_to_curses_color(b: int, g: int, r: int) -> int:
    """Map a BGR pixel to the nearest curses color constant."""
    # Find dominant channel(s)
    mx = max(r, g, b)
    if mx < 40:
        return curses.COLOR_WHITE  # Very dark → just use white chars on default bg

    # Normalize
    rn = r / mx
    gn = g / mx
    bn = b / mx

    threshold = 0.6

    r_on = rn > threshold
    g_on = gn > threshold
    b_on = bn > threshold

    if r_on and g_on and b_on:
        return curses.COLOR_WHITE
    elif r_on and g_on:
        return curses.COLOR_YELLOW
    elif r_on and b_on:
        return curses.COLOR_MAGENTA
    elif g_on and b_on:
        return curses.COLOR_CYAN
    elif r_on:
        return curses.COLOR_RED
    elif g_on:
        return curses.COLOR_GREEN
    elif b_on:
        return curses.COLOR_BLUE
    else:
        return curses.COLOR_WHITE


class Renderer:
    """Fullscreen terminal renderer using curses."""

    def __init__(self):
        self._stdscr = None
        self._color_map = {}
        self._fps_history = []
        self._last_frame_time = 0

    def init(self, stdscr):
        """Initialize the renderer with a curses screen."""
        self._stdscr = stdscr
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(True)  # Non-blocking getch
        stdscr.timeout(0)
        self._color_map = _init_colors()

    def get_size(self) -> tuple[int, int]:
        """Get terminal size as (width, height) in characters.

        Reserves 1 row at the bottom for the status bar.
        """
        max_y, max_x = self._stdscr.getmaxyx()
        # Reserve 1 row for status bar
        return max_x, max_y - 1

    def get_key(self) -> int:
        """Non-blocking key read. Returns -1 if no key pressed."""
        try:
            return self._stdscr.getch()
        except curses.error:
            return -1

    def render_frame(self, lines: list[str], color_frame=None, use_color: bool = False):
        """Render ASCII lines to the terminal.

        Args:
            lines: List of ASCII strings to display.
            color_frame: Optional BGR numpy array for colored rendering.
            use_color: Whether to apply color.
        """
        stdscr = self._stdscr
        max_y, max_x = stdscr.getmaxyx()

        try:
            stdscr.erase()

            for y, line in enumerate(lines):
                if y >= max_y - 1:  # Leave room for status bar
                    break

                if use_color and color_frame is not None:
                    # Render character by character with color
                    for x, ch in enumerate(line):
                        if x >= max_x - 1:
                            break
                        try:
                            b, g, r = color_frame[y, x]
                            cc = bgr_to_curses_color(int(b), int(g), int(r))
                            pair_id = self._color_map.get(cc, 0)
                            stdscr.addch(y, x, ch, curses.color_pair(pair_id))
                        except curses.error:
                            pass
                else:
                    # Fast monochrome rendering — whole line at once
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
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(status_y, 0, status.ljust(max_x - 1))
            stdscr.attroff(curses.A_REVERSE)
        except curses.error:
            pass

    def refresh(self):
        """Push the frame to the terminal."""
        self._stdscr.refresh()

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
