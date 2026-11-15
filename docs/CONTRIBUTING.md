# Contributing to QR Code Pretty

## Table of Contents

- [Requirements](#requirements)
- [Setting Up Development Environment](#setting-up-development-environment)
- [Building the Package](#building-the-package)
- [Testing](#testing)
- [Releases](#releases)

## Development

### Requirements

- Python 3.10 or higher (Python 3.11+ for release automation scripts)
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

The Nix shells provide development dependencies but do not install uv. Install
uv separately if you want to use the locked workflow below.

#### Using uv

```bash
# Clone the repository
git clone https://github.com/mrinfinidy/qrcode-pretty.git
cd qrcode-pretty

# Create/sync the environment, including development dependencies, from uv.lock
uv sync --locked

# Run the tool without changing the lockfile
uv run --locked qrcode-pretty -d "test"
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

# Install the project and test runner
python -m pip install -e . pytest

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

# The wheel (.whl) and source distribution (.tar.gz) are written to dist/.
```

### Testing

The preferred workflow matches CI and uses the committed lockfile:

```bash
uv sync --locked
uv run --locked pytest
```

If you used the pip/venv setup instead, activate that environment and run
`python -m pytest`. This alternative does not use `uv.lock`.

For local Debian/Ubuntu/Arch build and installation checks, see
[Packaging development and troubleshooting](../PACKAGING.md).

### Releases

Maintainers use the [coordinated release process](RELEASING.md): automated
preparation PR, build/install checks, then one protected approval for PyPI,
GitHub assets and the AUR push. No manual packaging commands are needed for a
normal release. Do not manually tag an unprepared revision.
