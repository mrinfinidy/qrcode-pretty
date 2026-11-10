"""Tests for CLI help handling (no image generation involved)."""

import pytest

import qrcode_pretty.entrypoint as entrypoint


def test_long_help_exits_successfully(capsys):
    with pytest.raises(SystemExit) as exc_info:
        entrypoint.main(["--help"])
    assert exc_info.value.code in (0, None)
    out = capsys.readouterr().out
    assert "Usage: qrcode-pretty" in out


def test_short_help_exits_successfully(capsys):
    with pytest.raises(SystemExit) as exc_info:
        entrypoint.main(["-h"])
    assert exc_info.value.code in (0, None)
    assert "Usage: qrcode-pretty" in capsys.readouterr().out
