#!/usr/bin/env bash
# Runs in an Arch container. makepkg must never run as root.
set -euo pipefail
pacman -Syu --noconfirm --needed base-devel git python python-qrcode python-pillow python-build python-installer python-hatchling
useradd --create-home builder
mkdir -p /build
cp /source/PKGBUILD /build/
chown -R builder:builder /build
cd /build
if [[ "${LOCAL_SOURCE:-false}" == true ]]; then
  # PR validation only: package this exact checkout, before its tag exists.
  mkdir -p /local-source/qrcode-pretty
  cp -a /source/. /local-source/qrcode-pretty/
  git -C /local-source/qrcode-pretty init
  git -C /local-source/qrcode-pretty -c user.name=CI -c user.email=ci@example.invalid add .
  git -C /local-source/qrcode-pretty -c user.name=CI -c user.email=ci@example.invalid commit -m source
  sha=$(git -C /local-source/qrcode-pretty rev-parse HEAD)
  sed -i "s|git+https://github.com/mrinfinidy/qrcode-pretty.git#tag=\${pkgver}|git+file:///local-source/qrcode-pretty#commit=$sha|" PKGBUILD
  chown -R builder:builder /build /local-source
  export GIT_ALLOW_PROTOCOL=file:https
fi
runuser -u builder -- makepkg --cleanbuild --noconfirm
pacman -U --noconfirm /build/*.pkg.tar.zst
useradd --create-home tester
cd /tmp
runuser -u tester -- python /source/scripts/release/smoke.py
pacman -R --noconfirm qrcode-pretty
test ! -e /usr/share/qrcode-pretty/assets/default.png
cd /build
runuser -u builder -- bash -euo pipefail -c 'makepkg --printsrcinfo > .SRCINFO.tmp; test -s .SRCINFO.tmp; mv .SRCINFO.tmp .SRCINFO'
if [[ "${LOCAL_SOURCE:-false}" != true ]]; then
  # Ensure the recipe actually fetched the intended immutable release commit.
  test "$(git -C src/qrcode-pretty rev-parse HEAD)" = "${RELEASE_SHA:?}"
fi
cp PKGBUILD /out/PKGBUILD
cp .SRCINFO /out/aur.SRCINFO
pacman -Q > /out/arch-build.txt
