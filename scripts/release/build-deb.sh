#!/usr/bin/env bash
# Runs as root inside a disposable matching distribution build container.
set -euo pipefail
suffix=${1:?deb13 or ubuntu24.04 required}
[[ "$suffix" == deb13 || "$suffix" == ubuntu24.04 ]]
export DEBIAN_FRONTEND=noninteractive
# Ubuntu's PEP 517 pybuild plugin is in universe.
if [[ "$suffix" == ubuntu24.04 ]]; then
  sed -i '/^Components:/ { /universe/! s/$/ universe/; }' /etc/apt/sources.list.d/ubuntu.sources
fi
apt-get update
apt-get install -y --no-install-recommends build-essential devscripts equivs lintian python3
mkdir -p /build/qrcode-pretty
cp -a /source/. /build/qrcode-pretty/
cd /build/qrcode-pretty
apt-get build-dep -y --no-install-recommends .
useradd --create-home builder
chown -R builder:builder /build
base=$(dpkg-parsechangelog -S Version)
export DEBFULLNAME="qrcode-pretty release"
export DEBEMAIL="qrcode-pretty-release@users.noreply.github.com"
runuser -u builder -- dch --newversion "$base+$suffix" --distribution UNRELEASED "Binary build for $suffix."
runuser -u builder -- dpkg-buildpackage -us -uc -b
runuser -u builder -- lintian --fail-on error /build/*.deb /build/*.changes
cp /build/*.deb /build/*.changes /build/*.buildinfo /out/
{
  cat /etc/os-release
  printf '\nSOURCE_DATE_EPOCH=%s\n' "${SOURCE_DATE_EPOCH:?}"
  dpkg-query -W
} > "/out/$suffix-build.txt"
