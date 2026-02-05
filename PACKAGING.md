# Packaging Guide for qrcode-pretty

This document explains how to build and test packages for Debian/Ubuntu and Arch Linux.

## Prerequisites

### For Debian/Ubuntu Packaging

Install build dependencies:

```bash
sudo apt-get install debhelper dh-python python3-all python3-setuptools \
  python3-hatchling pybuild-plugin-pyproject python3-qrcode python3-pil
```

### For Arch Linux Packaging

Install build dependencies:

```bash
sudo pacman -S base-devel python python-build python-installer python-hatchling
```

---

## Building Debian/Ubuntu Package (.deb)

### Build the Package

From the project root directory:

```bash
# Build the .deb package
dpkg-buildpackage -us -uc -b

# The package will be created in the parent directory, e.g.:
# ../qrcode-pretty_1.0.3-1_all.deb
```

###Testing the Package

```bash
# Install the package
sudo dpkg -i ../qrcode-pretty_1.0.3-1_all.deb

# Install any missing dependencies
sudo apt-get install -f

# Test basic functionality
qrcode-pretty --data "https://example.com" --output /tmp

# Test with default image
qrcode-pretty --data "test" --image default --output /tmp

# Verify installed files
dpkg -L qrcode-pretty

# Check that the wrapper is working
which qrcode-pretty  # Should show /usr/bin/qrcode-pretty
file /usr/bin/qrcode-pretty  # Should show Python script

# Uninstall (removes all package files)
sudo apt-get remove qrcode-pretty

# Verify removal
dpkg -l | grep qrcode-pretty
```

### Troubleshooting

**Missing dependencies:**

```bash
sudo apt-get install -f
```

**Check package contents:**

```bash
dpkg-deb -c ../qrcode-pretty_1.0.3-1_all.deb
```

**Lintian checks (optional):**

```bash
lintian ../qrcode-pretty_1.0.3-1_all.deb
```

---

## Building Arch Linux Package

### Build the Package

```bash
# Build the package
makepkg -si

# Or just build without installing
makepkg

# The package will be created in the current directory, e.g.:
# qrcode-pretty-1.0.3-1-any.pkg.tar.zst
```

### Generate .SRCINFO (for AUR)

```bash
makepkg --printsrcinfo > .SRCINFO
```

### Testing the Package

```bash
# Install
sudo pacman -U qrcode-pretty-1.0.3-1-any.pkg.tar.zst

# Test basic functionality
qrcode-pretty --data "https://example.com" --output /tmp

# Test with default image
qrcode-pretty --data "test" --image default --output /tmp

# Test with custom image
qrcode-pretty --data "test" --image /path/to/your/logo.png --output /tmp

# List installed files
pacman -Ql qrcode-pretty

# Check binary
which qrcode-pretty

# Uninstall
sudo pacman -R qrcode-pretty

# Verify removal
pacman -Q qrcode-pretty 2>&1 | grep "was not found"
```

### Publishing to AUR

1. **Create AUR account** at https://aur.archlinux.org/

2. **Clone the AUR repository:**

```bash
git clone ssh://aur@aur.archlinux.org/qrcode-pretty.git aur-qrcode-pretty
cd aur-qrcode-pretty
```

3. **Add packaging files:**

```bash
# Copy PKGBUILD from project root
cp ../PKGBUILD .

# Generate .SRCINFO
makepkg --printsrcinfo > .SRCINFO
```

4. **Commit and push:**

```bash
git add PKGBUILD .SRCINFO
git commit -m "Commit message here"
git push
```

5. **Update for new versions:**

```bash
# Update pkgver in PKGBUILD
# Regenerate .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# Commit and push
git add PKGBUILD .SRCINFO
git commit -m "Update to version X.Y.Z"
git push
```

---

## Asset Path Handling

The `assets/default.png` file is **included** with all package installations. The package includes a wrapper script that ensures the default image is available regardless of installation method.

### How Asset Resolution Works

Both Debian and Arch packages use a wrapper script approach:

1. **Assets are installed** to `/usr/share/qrcode-pretty/assets/default.png`
2. **Real binary** is moved to `/usr/lib/qrcode-pretty/qrcode-pretty-real`
3. **Wrapper script** at `/usr/bin/qrcode-pretty` sets `DEFAULT_IMAGE` environment variable
4. **Python code** searches for the default image in priority order:
   - Environment variable `DEFAULT_IMAGE` (highest priority)
   - `/usr/share/qrcode-pretty/assets/default.png` (system-wide)
   - `$PREFIX/share/qrcode-pretty/assets/default.png` (pip/venv)
   - `./assets/default.png` (local development)
   - Relative to package directory (fallback)

### Using the Default Image

```bash
# Use the bundled default image
qrcode-pretty --data "test" --image default --output /tmp

# Use your own image
qrcode-pretty --data "test" --image /path/to/your/logo.png --output /tmp

# No image (QR code only)
qrcode-pretty --data "test" --output /tmp
```

### Testing Asset Resolution

```bash
# Check that assets are installed (Debian/Ubuntu)
ls -la /usr/share/qrcode-pretty/assets/default.png

# Check that assets are installed (Arch)
pacman -Ql qrcode-pretty | grep default.png

# Test that default image works
qrcode-pretty --data "test" --image default --output /tmp

# Override with custom path
DEFAULT_IMAGE=/path/to/custom.png qrcode-pretty --data "test" --image default --output /tmp
```

### Asset Cleanup

Assets are properly removed when uninstalling:

- **Debian/Ubuntu**: The `postrm` script removes `/usr/share/qrcode-pretty` and `/usr/lib/qrcode-pretty`
- **Arch Linux**: Standard pacman removal handles all installed files including assets

---

## Version Updates

When releasing a new version:

1. **Update version** in `pyproject.toml` or run `uv version --bump patch`
2. **Update Debian changelog:**
   ```bash
   dch -v 1.0.3-1 "New upstream release"
   ```
3. **Update PKGBUILD** `pkgver` and `pkgrel`
4. **Rebuild and test** all packages
5. **Commit changes** and tag release
6. **Publish** to PyPI and AUR

---

## PyPI Publishing

### GitHub CD

This section assumes that the version has been updated (see previous section _Version Updates_)

This repository has a CD defined in GitHub Actions. It runs based on git tags.
The CD automatically builds and publishes the package using uv.

```bash
# Create version tag matching the current pyproject.toml version
git tag <version>

# Push version tag
git push origin <version>

```

### Manually using uv

```bash
# Build the package
uv build

# (Optional) Publish to TestPyPI
uv publish --publish-url https://test.pypi.org/legacy/

# Publish
uv publish
```

### Manually using pip

#### Build for PyPI

```bash
# Install build tools
pip install build twine

# Build wheel and source distribution
python -m build

# Output in dist/ e.g.:
# - qrcode_pretty-1.0.3-py3-none-any.whl
# - qrcode_pretty-1.0.3.tar.gz
```

#### Publish to PyPI

```bash
# Upload to Test PyPI (recommended first)
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ qrcode-pretty

# Upload to PyPI
twine upload dist/*
```

---

## Files Overview

### Debian Packaging Files

- `debian/control` - Package metadata and dependencies
- `debian/rules` - Build instructions
- `debian/changelog` - Version history
- `debian/compat` - Debhelper compatibility level
- `debian/copyright` - License information
- `debian/qrcode-pretty.wrapper` - Shell wrapper script
- `debian/source/format` - Source package format

### Arch Packaging Files

- `PKGBUILD` - Build script and metadata
- `.SRCINFO` - Metadata for AUR (generated from PKGBUILD)

### Python Code Enhancements

- `src/qrcode_pretty/qr_code_generator.py` - Added `find_default_image()` function

---

## Support

For issues or questions:

- **GitHub Issues**: https://github.com/mrinfinidy/qrcode-pretty/issues
- **Email**: mail@afkdev8.com
