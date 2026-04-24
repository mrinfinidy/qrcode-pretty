# Contributing to QR Code Pretty

## Table of Contents

- [Requirements](#requirements)
- [Setting Up Development Environment](#setting-up-development-environment)
- [Building the Package](#building-the-package)
- [Testing](#testing)

## Development

### Requirements

- Python 3.8 or higher
- Dependencies (automatically installed):
  - qrcode[pil] >= 7.0
  - pillow >= 9.0

### Setting Up Development Environment

#### Using NixOS

```bash
# Clone the repository
git clone https://github.com/mrinfinidy/qrcode-pretty.git
cd qrcode-pretty

# Enter development shell
nix-shell

# Or use the flake development shell
nix develop
```

#### Using uv

```bash
# Clone the repository
git clone https://github.com/mrinfinidy/qrcode-pretty.git
cd qrcode-pretty

# Create virtual environment and install in editable mode
uv venv
# or: .venv\Scripts\activate  # On Windows

uv pip install -e .

# Run the tool
uv run qrcode-pretty -d "test"
```

#### Using pip/venv

```bash
# Clone the repository
git clone https://github.com/mrinfinidy/qrcode-pretty.git
cd qrcode-pretty

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# or: .venv\Scripts\activate  # On Windows

# Install in editable mode
pip install -e .

# Run the tool
qrcode-pretty -d "test"
```

### Building the Package

#### With Nix

```bash
# Build with Nix
nix build .#qrcode-pretty

# Result will be in ./result/
./result/bin/qrcode-pretty --help
```

#### With uv

```bash
# Build wheel and source distribution
uv build

# Output will be in dist/ e.g.:
# - dist/qrcode_pretty-1.0.0-py3-none-any.whl
# - dist/qrcode_pretty-1.0.0.tar.gz
```

### Testing

#### uv

This section assumes that you have successfully set up a development environment with uv.

```bash
# Run tests
uv run pytest
```
