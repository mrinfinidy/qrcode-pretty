# Packaging development and troubleshooting

> **Normal releases require no manual packaging commands.** Use the
> [automated release process](docs/RELEASING.md): the pipeline builds, tests, and
> publishes packages after the preparation PR and release approval. Skip the
> instructions below when releasing a new upstream version.

This guide is for contributors and maintainers who need to:

- Reproduce a package-build or installation failure locally.
- Test changes to dependencies, wrappers, assets, or packaging metadata.
- Maintain packaging-only fixes without republishing an upstream Python release.
- Build packages manually when CI is unavailable.

For installing published packages, see the [README](README.md#debianubuntu).
For publication credentials, approvals, and recovery, see
[Coordinated releases](docs/RELEASING.md).

## Test packaging changes locally

From the repository root, use the same build/install checks as CI:

```sh
bash scripts/release/check-containers.sh deb13
bash scripts/release/check-containers.sh ubuntu24.04
bash scripts/release/check-containers.sh arch
```

The helper defaults to Docker. It copies the current working tree, builds in
disposable containers, tests installation and removal, and deletes temporary
outputs. It does not publish anything. The Arch check overrides the tag-pinned
source temporarily so it tests your current code rather than a previous release.

For an already configured rootless Podman environment on Linux, set
`CONTAINER_ENGINE=podman PODMAN_KEEP_ID=true` before a helper invocation. The
keep-id mode exposes ownership problems that Podman's default mapping can hide.

Do not run `build-deb.sh`, `test-deb.sh`, or `build-arch.sh` directly on your host:
they install packages and create users inside their disposable containers.

## Debian / Ubuntu development builds

The tested targets are **Debian 13** and **Ubuntu 24.04 LTS**. Use a matching
container/VM, especially when developing on NixOS: dpkg alone is not a complete
Debian build environment.

To retain a package for investigation, run these commands from the complete
checkout inside that environment. Install dependencies with sudo, then build as
an ordinary user:

```sh
sudo apt-get update
sudo apt-get install build-essential devscripts equivs lintian
sudo apt-get build-dep .
dpkg-buildpackage -us -uc -b
lintian ../qrcode-pretty_*.deb
```

Ubuntu needs the universe component for `pybuild-plugin-pyproject`. This is a
binary-only build; the existing `3.0 (quilt)` source format does not make it a
source upload or PPA publication.

Packaging files are under `debian/`. Compatibility level 13 is declared through
`debhelper-compat` in control, not a separate compat file. Pybuild runs pytest
with distro Python dependencies, without uv or network dependency resolution
during the build. Lintian errors fail CI; the missing man page is a documented
warning, not a suppressed error.

CI adds a distribution suffix to the Debian changelog version in its temporary
workspace, producing `X.Y.Z-1+deb13` and `X.Y.Z-1+ubuntu24.04`. A direct manual
build keeps the version in your local changelog. `Architecture: all` does not
imply compatibility with untested distribution versions.

## Arch development builds

Use a real Arch environment and run makepkg as an ordinary user:

```sh
sudo pacman -S --needed base-devel git python python-build python-installer \
  python-hatchling python-qrcode python-pillow
makepkg --cleanbuild
```

The committed PKGBUILD fetches the immutable upstream tag. This direct command
therefore **does not test uncommitted application-code changes**. Use the
container helper above to test the current working tree before its tag exists.
The recipe uses distro dependencies and builds a wheel without downloading
Python build dependencies.

## Packaging-only maintenance

Packaging-only fixes are distinct from new upstream releases. The coordinated
workflow publishes upstream version releases; it does not automatically publish
a standalone Debian revision or AUR pkgrel update. Review and validate the
appropriate packaging/delivery path separately rather than republishing PyPI.

### Updating AUR packaging manually

The separate AUR repository is
`ssh://aur@aur.archlinux.org/qrcode-pretty.git`. Review its current remote state
before changing packaging. For a packaging-only fix at the same upstream
version, increment pkgrel in its PKGBUILD.

In that AUR checkout, after reviewing/updating PKGBUILD:

```sh
makepkg --cleanbuild
makepkg --printsrcinfo > .SRCINFO.tmp &&
  test -s .SRCINFO.tmp &&
  mv .SRCINFO.tmp .SRCINFO
git diff --check
git diff -- PKGBUILD .SRCINFO
```

Generate metadata in a real Arch environment with a working makepkg
configuration. The temporary file prevents a failed generation from truncating
the existing `.SRCINFO`.

A maintainer can then commit and push the reviewed files without force-pushing.
Keep this repository's PKGBUILD aligned with deliberate packaging changes.
Automatic release recovery will not overwrite conflicting same-version AUR
packaging or downgrade a newer remote version.

## Asset and installation troubleshooting

Debian/Arch install the system image at
`/usr/share/qrcode-pretty/assets/default.png`. Their wrapper sets DEFAULT_IMAGE
unless the user supplied an override. Python distributions built by the new
pipeline also include package-relative image data; the 1.1.1 distributions did
not bundle that image.

Install checks run away from the checkout so a local `assets/default.png` cannot
mask a missing packaged image. They test ordinary generation, default/custom
images, the environment override, and package removal. When investigating a
failure, check the installed wrapper and image path, not only source-tree tests.
