"""Compare generated pixels, independent of PNG compression and metadata."""
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image


@pytest.mark.parametrize("subprocess_cli", [True, False])
def test_qrcode_generation_test_data(tmp_path, subprocess_cli):
    reference = Path(__file__).parent / "reference_images/simple_reference.png"
    args = ["-d", "test", "--output", str(tmp_path)]
    if subprocess_cli:
        result = subprocess.run(
            [sys.executable, "-m", "qrcode_pretty.entrypoint", *args],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
    else:
        from qrcode_pretty.entrypoint import main
        assert main(args) is None
    with Image.open(tmp_path / "qrcode.png") as actual, Image.open(reference) as expected:
        assert actual.size == expected.size
        assert actual.convert("RGBA").tobytes() == expected.convert("RGBA").tobytes()
