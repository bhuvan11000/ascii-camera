"""
Camera capture module — wraps OpenCV VideoCapture with resource management.
"""

import cv2
import numpy as np


class Camera:
    """Manages webcam capture with automatic resource cleanup."""

    def __init__(self, device: int = 0, target_fps: int = 30):
        """Initialize camera capture.

        Args:
            device: Camera device index (0 = default camera).
            target_fps: Desired capture frame rate.
        """
        self.device = device
        self.target_fps = target_fps
        self._cap = None

    def open(self) -> bool:
        """Open the camera device. Returns True on success."""
        self._cap = cv2.VideoCapture(self.device)
        if not self._cap.isOpened():
            return False

        # Try to set FPS (camera may ignore this)
        self._cap.set(cv2.CAP_PROP_FPS, self.target_fps)

        # Use a smaller resolution for faster processing
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        return True

    def read_frame(self) -> np.ndarray | None:
        """Read a single frame from the camera.

        Returns:
            BGR numpy array, or None if read failed.
        """
        if self._cap is None or not self._cap.isOpened():
            return None

        ret, frame = self._cap.read()
        if not ret:
            return None

        # Mirror horizontally so it feels like a real mirror/selfie
        frame = cv2.flip(frame, 1)
        return frame

    def is_opened(self) -> bool:
        """Check if camera is currently open."""
        return self._cap is not None and self._cap.isOpened()

    def close(self):
        """Release the camera device."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
