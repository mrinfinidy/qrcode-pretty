#!/usr/bin/env python3
"""Exercise the installed CLI away from source and verify real output images."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image


def main():
    executable = shutil.which("qrcode-pretty")
    if not executable:
        raise RuntimeError("Installed qrcode-pretty entrypoint is missing")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run([executable, "--help"], cwd=root, check=True)
        custom = root / "custom.png"
        Image.new("RGB", (64, 64), "red").save(custom)
        cases = [([], {}), (["--image", "default"], {}),
                 (["--image", str(custom)], {}),
                 (["--image", "default"], {"DEFAULT_IMAGE": str(custom)})]
        for i, (args, env) in enumerate(cases):
            out = root / f"case-{i}"
            subprocess.run([executable, "--data", "release-smoke", "--output", str(out), *args],
                           cwd=root, env={**os.environ, **env}, check=True)
            with Image.open(out / "qrcode.png") as image:
                image.load()
                assert image.width > 0 and image.height > 0
                assert len(image.convert("RGB").getcolors(image.width * image.height) or []) > 1
    print("Installed CLI, images and default-asset lookup passed.")


if __name__ == "__main__":
    main()
