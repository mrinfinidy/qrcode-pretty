import os
import sys

def find_default_image():
    """Find the default image in standard locations.
    
    Searches for the default image in the following order:
    1. Environment variable DEFAULT_IMAGE (highest priority)
    2. System-wide install: /usr/share/qrcode-pretty/assets/default.png
    3. Python prefix install: {sys.prefix}/share/qrcode-pretty/assets/default.png
    4. Local development: ./assets/default.png
    5. Package relative: ../../assets/default.png (from module directory)
    
    Returns:
        str: Path to the default image, or fallback to ./assets/default.png
    """
    search_paths = [
        os.environ.get("DEFAULT_IMAGE"),
        "/usr/share/qrcode-pretty/assets/default.png",
        os.path.join(sys.prefix, "share/qrcode-pretty/assets/default.png"),
        "./assets/default.png",
        os.path.join(os.path.dirname(__file__), "..", "..", "assets", "default.png"),
    ]
    
    for path in search_paths:
        if path and os.path.isfile(path):
            return path
    
    return "./assets/default.png"
