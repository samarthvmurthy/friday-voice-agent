import mss
from PIL import Image
import io


def capture_screen(monitor_index=1):
    """Capture the primary screen and return as PIL Image."""
    with mss.mss() as sct:
        monitor = sct.monitors[monitor_index]
        raw = sct.grab(monitor)
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
        return img


def image_to_bytes(img: Image.Image) -> bytes:
    """Convert PIL Image to PNG bytes for Gemini."""
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def get_screen_size():
    with mss.mss() as sct:
        m = sct.monitors[1]
        return m["width"], m["height"]
