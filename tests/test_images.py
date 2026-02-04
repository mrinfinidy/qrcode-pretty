"""Test suite to verify generated QR code images match expected outputs."""

import hashlib
import subprocess
from pathlib import Path

import pytest


def get_image_hash(image_path: Path) -> str:
    """Calculate SHA256 hash of an image file."""
    sha256_hash = hashlib.sha256()
    with open(image_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


@pytest.fixture
def output_dir(tmp_path):
    """Provide a temporary directory for test outputs."""
    return tmp_path


@pytest.fixture
def reference_images_dir():
    """Provide path to reference images directory."""
    return Path("tests/reference_images")


def test_qrcode_generation_test_data(output_dir, reference_images_dir):
    """Test QR code generation for 'test' data matches reference image."""
    generated_image = output_dir / "qrcode.png"
    reference_image = reference_images_dir / "simple.png"

    assert reference_image.exists(), f"Reference image not found at {reference_image}"

    cmd = ["uv", "run", "qrcode-pretty", "-d", "test", "--output", str(output_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert generated_image.exists(), f"Generated image not found at {generated_image}"

    generated_hash = get_image_hash(generated_image)
    reference_hash = get_image_hash(reference_image)

    assert (
        generated_hash == reference_hash
    ), f"Image hash mismatch:\n  Generated: {generated_hash}\n  Reference: {reference_hash}"
