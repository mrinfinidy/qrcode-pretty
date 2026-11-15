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
run_args=()
if [[ "${PODMAN_KEEP_ID:-false}" == true ]]; then
  [[ "$engine" == podman ]] || { echo "PODMAN_KEEP_ID requires podman" >&2; exit 1; }
  # Map the host user to a non-root container UID while running builds as root.
  # This exposes ownership bugs hidden by rootless Podman's default root mapping.
  run_args=(--userns=keep-id --user=0:0)
fi
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir "$tmp/source" "$tmp/packages"
git ls-files -co --exclude-standard -z | tar --null -T - -cf "$tmp/source.tar"
tar -xf "$tmp/source.tar" -C "$tmp/source"
epoch=$(git show -s --format=%ct HEAD)
"$engine" pull "$image"
image_id=$("$engine" image inspect --format '{{.Id}}' "$image")
if [[ "$target" == arch ]]; then
  "$engine" run --rm "${run_args[@]}" -e LOCAL_SOURCE=true \
    -v "$tmp/source:/source:ro" -v "$tmp/packages:/out" \
    "$image_id" bash /source/scripts/release/build-arch.sh
else
  "$engine" run --rm "${run_args[@]}" -e SOURCE_DATE_EPOCH="$epoch" \
    -v "$tmp/source:/source:ro" -v "$tmp/packages:/out" \
    "$image_id" bash /source/scripts/release/build-deb.sh "$target"
  "$engine" run --rm "${run_args[@]}" \
    -v "$tmp/packages:/packages:ro" -v "$tmp/source/scripts/release:/checks:ro" \
    "$image_id" bash /checks/test-deb.sh
fi
# Match CI's host-side provenance write without modifying root-owned records.
"$engine" image inspect --format '{{json .RepoDigests}}' "$image" > "$tmp/packages/$target-image.json"
test -s "$tmp/packages/$target-image.json"
test -r "$tmp/packages/$target-build.txt"
if [[ "${PODMAN_KEEP_ID:-false}" == true ]]; then
  test ! -w "$tmp/packages/$target-build.txt"
  echo "Verified container build record is not writable by the host user."
fi
printf 'Build and installation checks passed: %s\n' "$target"
