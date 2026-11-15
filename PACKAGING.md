# Packaging qrcode-pretty

For release preparation, approvals, publication credentials, artifacts and
recovery, see [Coordinated releases](docs/RELEASING.md). A normal release does not
require manually synchronizing packaging versions.

## Debian 13 / Ubuntu 24.04

CI builds each target independently using its own distro-provided build
dependencies. The generated binary versions distinguish the targets:

- Debian 13: `X.Y.Z-1+deb13`
- Ubuntu 24.04: `X.Y.Z-1+ubuntu24.04`

Both packages are `Architecture: all`; this does not imply compatibility with
untested Debian/Ubuntu versions. Build records and checksums accompany GitHub
Release downloads. No APT repository or PPA is provided.

### Install a release download

Download the package matching your distribution from GitHub Releases, verify its
checksum against `SHA256SUMS`, then install that local file with apt:

```sh
sudo apt install ./qrcode-pretty_*.deb
qrcode-pretty --help
qrcode-pretty --data 'https://example.com' --image default --output /tmp/qr-test
sudo apt purge qrcode-pretty
```

Keep only the intended distribution's package in the download directory before
using the wildcard.

### Manual development build (inside Debian/Ubuntu)

Use a disposable container/VM, especially when developing on NixOS. Do not assume
that installing dpkg alone provides a Debian build environment.

```sh
sudo apt-get update
sudo apt-get install build-essential devscripts equivs lintian
sudo apt-get build-dep .
dpkg-buildpackage -us -uc -b
lintian ../qrcode-pretty_*.deb
```

Run from the complete repository checkout. Ubuntu needs the universe component
for pybuild-plugin-pyproject. This is a binary-only build; the existing
`3.0 (quilt)` source format does not make it a source upload or PPA publication.

Packaging files are under `debian/`. Compatibility level 13 is declared with
`debhelper-compat` in control; there is no separate compat file. Unit tests use
pytest and distro Python dependencies, without uv or network dependency
resolution during the build.

## Arch Linux / AUR

The fixed-version PKGBUILD fetches the immutable upstream tag. It uses system
Python dependencies and builds a wheel without downloading build dependencies.

In a real Arch environment:

```sh
sudo pacman -S --needed base-devel git python python-build python-installer \
  python-hatchling python-qrcode python-pillow
makepkg --cleanbuild
```

For automatic pushes, credentials, safe metadata generation and packaging-only
maintenance, see [AUR publishing](AUR_PUBLISHING_GUIDE.md).

## Default-image assets

Debian/Arch install the system image at
`/usr/share/qrcode-pretty/assets/default.png`. Their wrapper sets DEFAULT_IMAGE
unless the user supplied an override. Python wheel/sdist installs also include
package-relative image data.

Install tests run away from the source checkout so a local `assets/default.png`
cannot mask a missing packaged image. They test normal generation, default and
custom images, the environment override, and package removal.
