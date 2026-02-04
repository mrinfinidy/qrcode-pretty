# QR Code Pretty

![Banner](./samples/banner.png)

## Overview

Generate pretty QR codes.

QR Code Pretty uses the [python-qrcode](https://github.com/lincolnloop/python-qrcode) library to generate qr codes
and provides various options to customize the qrcode.
You can adjust style, color and add an image in the middle.
Check out the usage for all available options.

## Installation

### NixOS

This tool is packaged as a NixOS package. You can install it using the following flake input:

```nix
qrcode-pretty = {
  url = "github:mrinfinidy/qrcode-pretty";
  inputs.nixpkgs.follows = "nixpkgs";
};
```

Add the flake input to the outputs:

```nix
outputs = {
  # your other outputs
  qrcode-pretty,
  ...
}@inputs:
```

Then add to your home-manager config:

```nix
home-manager.users.<your-user> = {
    home.packages = [
        (inputs.qrcode-pretty.packages.${pkgs.system}.default)
    ];
};
```

Or build and run directly:

```bash
# Build with Nix
nix build github:mrinfinidy/qrcode-pretty

# Run from local checkout
nix run .#qrcode-pretty -- -d "your data here"
```

Or to test without permanent installation:

```bash
nix run github:mrinfinidy/qrcode-pretty --override-input nixpkgs nixpkgs
```

### Debian/Ubuntu

Download and install the `.deb` package from the [releases page](https://github.com/mrinfinidy/qrcode-pretty/releases):

```bash
# Download the latest .deb package
wget https://github.com/mrinfinidy/qrcode-pretty/releases/download/<version>/qrcode-pretty_<version>-1_all.deb

# Install the package
sudo dpkg -i qrcode-pretty_<version>-1_all.deb

# Install dependencies if needed
sudo apt-get install -f
```

Or build from source (see [PACKAGING.md](PACKAGING.md) for details):

```bash
dpkg-buildpackage -us -uc -b
sudo dpkg -i ../qrcode-pretty_<version>-1_all.deb
```

### Arch Linux (AUR)

Install from the AUR using your preferred AUR helper:

```bash
# Using yay
yay -S qrcode-pretty

# Using paru
paru -S qrcode-pretty

# Or manually with makepkg
git clone https://aur.archlinux.org/qrcode-pretty.git
cd qrcode-pretty
makepkg -si
```

### Using uv

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver, which I prefer over pip/pipx:

```bash
uv tool install qrcode-pretty
```

### Using pipx

For installing as a standalone command-line tool:

```bash
pipx install qrcode-pretty
```

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

## Usage

QR Code Pretty provides the `qrcode-pretty` command-line tool.

### Basic Usage

Generate a QR code with minimal options:

```bash
qrcode-pretty -d "https://github.com/mrinfinidy/qrcode-pretty"
```

### Command-Line Options

Use `qrcode-pretty -h` to print all available options:

```
Options:
  -h, --help                              Show this help message and exit
  -d, --data <data>                       Data to encode in QR code (required)
  -i, --image <image>                     Input image file name
  -s, --style <style>                     Style for the QR code modules
      --style-inner <style>               Style for the inner eyes
      --style-outer <style>               Style for the outer eyes
  -b, --base <hex>                        Base color hex code (e.g. #000000)
  -n, --color-inner <hex>                 Inner eye color hex code
  -r, --color-outer <hex>                 Outer eye color hex code
  -o, --output <directory or filename>    Output directory path or filename (default: ~/Pictures/qrcode-pretty/qrcode.png)
      --svg                               Also generate SVG output
      --version <int>                     QR version (default: 5)
      --box-size <int>                    Box size in pixels (default: 10)
      --border <int>                      Border size in boxes (default: 4)
      --error-correction <L|M|Q|H>        Error correction level (default: H)

Available styles: square, gapped-square, circle, round, vertical-bars, horizontal-bars
```

**Note:** When embedding a center image (logo), it is recommended to use a high error correction level (default: H).

**About the `--image` option:**

- Use `--image /path/to/your/logo.png` to embed your own image in the QR code center
- Use `--image default` to use the bundled demonstration image (included with all installation methods)
- Omit `--image` to generate a QR code without a center image

### Sample Gallery

#### QR Code Github

![qrcode github cat](./samples/qrcode-cat.png)

`qrcode-pretty --data "https://github.com/mrinfinidy/qrcode-pretty" --image default --style round --style-inner round --style-outer round --base "#000000" --color-inner "#d3869b" --color-outer "#458588" --output "~/Pictures/"`

![qrcode github cat 2](./samples/qrcode-cat-2.png)

`qrcode-pretty --data "https://github.com/mrinfinidy/qrcode-pretty" --image default --style circle --style-inner round --style-outer round --base "#1d2021" --color-inner "#666341" --color-outer "#1d2021" --output "~/Pictures/"`

![qrcode github](./samples/qrcode-purple.png)

`qrcode-pretty --data "https://github.com/mrinfinidy/qrcode-pretty" --style round --style-inner round --style-outer round --base "#8e8ece" --color-inner "#6cf2e5" --color-outer "#40E0D0" --output "~/Pictures/"`

#### QR Code afkdev8 (my homepage)

![qrcode afkdev8 vertical-bars](./samples/qrcode-afkdev8-vertical.png)

`qrcode-pretty --data "https://www.afkdev8.com/" --image "~/Pictures/afkdev8-logo.png" --style vertical-bars --style-inner round --style-outer round --base "#000000" --color-inner "#000000" --color-outer "#000000" --output "~/Pictures/"`

![qrcode afkdev8 horizontal-bars](./samples/qrcode-afkdev-horizontal.png)

`qrcode-pretty --data "https://www.afkdev8.com/" --image "~/Pictures/afkdev8-logo-dark.png" --style horizontal-bars --style-inner round --style-outer round --base "#000000" --color-inner "#000000" --color-outer "#000000" --output "~/Pictures/"`

#### QR Code lemons

![qrcode lemons](./samples/qrcode-lemons.png)

`qrcode-pretty --data "lemons" --image "~/Pictures/lemons.png" --style square --style-inner circle --style-outer gapped-square --base "#000000" --color-inner "#000000" --color-outer "#000000" --output "~/Pictures/"`

## Package Information

This package follows modern Python packaging standards:

- **Package Name**: `qrcode-pretty`
- **Module Name**: `qrcode_pretty`
- **Build System**: [Hatchling](https://hatch.pypa.io/)
- **Configuration**: `pyproject.toml` (PEP 621 compliant)
- **Minimum Python**: 3.8+

### Project Structure

```
qrcode-pretty/
├── src/
│   └── qrcode_pretty/
│       ├── __init__.py
│       ├── entrypoint.py
│       ├── qr_code_generator.py
│       └── const.py
├── pyproject.toml
├── README.md
└── LICENSE
```

## Author

afkdev8 `<mail@afkdev8.com>`
