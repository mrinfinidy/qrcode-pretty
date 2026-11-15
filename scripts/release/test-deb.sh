#!/usr/bin/env bash
# Fresh runtime container, with neither the build tree nor its dependencies.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends /packages/*.deb
test -x /usr/bin/qrcode-pretty
test -r /usr/share/qrcode-pretty/assets/default.png
useradd --create-home tester
cd /tmp
runuser -u tester -- python3 /checks/smoke.py
dpkg-query -L qrcode-pretty
apt-get purge -y qrcode-pretty
test ! -e /usr/bin/qrcode-pretty
test ! -e /usr/lib/qrcode-pretty/qrcode-pretty-real
test ! -e /usr/share/qrcode-pretty/assets/default.png
