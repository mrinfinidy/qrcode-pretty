#!/usr/bin/env bash
# Non-publishing validation of the current working tree, including local edits.
set -euo pipefail
cd "$(dirname "$0")/../.."
target=${1:?Usage: check-containers.sh deb13|ubuntu24.04|arch}
case "$target" in
  deb13) image=docker.io/library/debian:13 ;;
  ubuntu24.04) image=docker.io/library/ubuntu:24.04 ;;
  arch) image=docker.io/library/archlinux:base-devel ;;
  *) echo "Unknown target: $target" >&2; exit 1 ;;
esac
engine=${CONTAINER_ENGINE:-docker}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir "$tmp/source" "$tmp/packages"
git ls-files -co --exclude-standard -z | tar --null -T - -cf "$tmp/source.tar"
tar -xf "$tmp/source.tar" -C "$tmp/source"
epoch=$(git show -s --format=%ct HEAD)
if [[ "$target" == arch ]]; then
  "$engine" run --rm -e LOCAL_SOURCE=true \
    -v "$tmp/source:/source:ro" -v "$tmp/packages:/out" \
    "$image" bash /source/scripts/release/build-arch.sh
else
  "$engine" run --rm -e SOURCE_DATE_EPOCH="$epoch" \
    -v "$tmp/source:/source:ro" -v "$tmp/packages:/out" \
    "$image" bash /source/scripts/release/build-deb.sh "$target"
  "$engine" run --rm \
    -v "$tmp/packages:/packages:ro" -v "$tmp/source/scripts/release:/checks:ro" \
    "$image" bash /checks/test-deb.sh
fi
printf 'Build and installation checks passed: %s\n' "$target"
