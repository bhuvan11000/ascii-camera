"""
ASCII art converter — maps pixel brightness to ASCII characters.
"""

import numpy as np

# ASCII character ramps ordered from darkest to brightest
ASCII_RAMP_DETAILED = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
ASCII_RAMP_SIMPLE = " .:-=+*#%@"


def frame_to_gray(frame: np.ndarray) -> np.ndarray:
    """Convert a BGR frame to grayscale."""
    # OpenCV loads as BGR
    import cv2
    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


def resize_frame(frame: np.ndarray, width: int, height: int) -> np.ndarray:
    """Resize frame to target dimensions.

    Terminal characters are ~2x taller than wide, so each 'pixel' in the
    terminal corresponds to roughly a 1:2 (w:h) block of actual pixels.
    We account for that by requesting exactly (width, height) from OpenCV,
    which means the caller must already factor in the aspect ratio.
    """
    import cv2
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)


def apply_contrast(gray: np.ndarray, factor: float = 1.0) -> np.ndarray:
    """Apply contrast adjustment. factor=1.0 is no change."""
    if factor == 1.0:
        return gray
    adjusted = 128 + factor * (gray.astype(np.float32) - 128)
    return np.clip(adjusted, 0, 255).astype(np.uint8)


def gray_to_ascii(gray: np.ndarray, ramp: str = None, invert: bool = False) -> list[str]:
    """Convert a grayscale image (2D numpy array) to lines of ASCII text.

    Args:
        gray: 2D uint8 array of shape (rows, cols).
        ramp: Character ramp string from dark to bright.
        invert: If True, bright pixels get dark characters and vice versa.

    Returns:
        List of strings, one per row.
    """
    if ramp is None:
        ramp = ASCII_RAMP_DETAILED

    if invert:
        ramp = ramp[::-1]

    ramp_len = len(ramp)
    # Map 0-255 to ramp indices
    indices = (gray.astype(np.float32) / 255.0 * (ramp_len - 1)).astype(np.int32)

    # Build lookup array for vectorized char mapping
    ramp_arr = np.array(list(ramp))
    char_matrix = ramp_arr[indices]

    # Join each row into a string
    lines = [''.join(row) for row in char_matrix]
    return lines


def frame_to_ascii(
    frame: np.ndarray,
    width: int,
    height: int,
    contrast: float = 1.0,
    invert: bool = False,
    ramp: str = None,
) -> list[str]:
    """Full pipeline: BGR frame → ASCII lines.

    Args:
        frame: Raw BGR frame from OpenCV.
        width: Target width in characters.
        height: Target height in characters.
        contrast: Contrast multiplier (1.0 = normal).
        invert: Invert brightness mapping.
        ramp: Custom ASCII character ramp.

    Returns:
        List of ASCII strings, one per terminal row.
    """
    gray = frame_to_gray(frame)
    gray = resize_frame(gray, width, height)
    gray = apply_contrast(gray, contrast)
    return gray_to_ascii(gray, ramp=ramp, invert=invert)


def frame_to_colored_ascii(
    frame: np.ndarray,
    width: int,
    height: int,
    contrast: float = 1.0,
    invert: bool = False,
    ramp: str = None,
) -> tuple[list[str], np.ndarray]:
    """Full pipeline: BGR frame → ASCII lines + color info.

    Returns:
        Tuple of (ascii_lines, color_frame) where color_frame is the
        resized BGR frame for extracting per-character colors.
    """
    import cv2

    gray = frame_to_gray(frame)
    resized_gray = resize_frame(gray, width, height)
    resized_gray = apply_contrast(resized_gray, contrast)
    lines = gray_to_ascii(resized_gray, ramp=ramp, invert=invert)

    # Resize original color frame to match
    color_frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

    return lines, color_frame
