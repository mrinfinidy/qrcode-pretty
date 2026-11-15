#!/usr/bin/env bash
# Called only inside the protected publisher, after verifying the artifact bundle.
set -euo pipefail
bundle=$(realpath "${1:?release bundle required}")
: "${AUR_SSH_PRIVATE_KEY:?Configure the dedicated AUR publisher key}"
: "${AUR_KNOWN_HOSTS:?Configure a verified aur.archlinux.org known_hosts entry}"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
umask 077
printf '%s\n' "$AUR_SSH_PRIVATE_KEY" > "$tmp/key"
printf '%s\n' "$AUR_KNOWN_HOSTS" > "$tmp/known_hosts"
unset AUR_SSH_PRIVATE_KEY AUR_KNOWN_HOSTS
export GIT_SSH_COMMAND="ssh -i $tmp/key -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$tmp/known_hosts"
git clone ssh://aur@aur.archlinux.org/qrcode-pretty.git "$tmp/aur"
cd "$tmp/aur"
# Never overwrite a same-version packaging edit or downgrade a newer release.
src_value() { awk -v key="$2" '$1 == key && $2 == "=" { print $3; exit }' "$1"; }
new_version="$(src_value "$bundle/aur.SRCINFO" pkgver)-$(src_value "$bundle/aur.SRCINFO" pkgrel)"
version_pattern='^[0-9]+\.[0-9]+\.[0-9]+-[1-9][0-9]*$'
[[ "$new_version" =~ $version_pattern ]] || { echo "Invalid generated AUR version" >&2; exit 1; }
if [[ -e PKGBUILD || -e .SRCINFO || -L PKGBUILD || -L .SRCINFO ]]; then
  if [[ ! -f PKGBUILD || ! -f .SRCINFO || -L PKGBUILD || -L .SRCINFO ]]; then
    echo "Unexpected remote AUR packaging layout; refusing to overwrite it." >&2
    exit 1
  fi
  old_version="$(src_value .SRCINFO pkgver)-$(src_value .SRCINFO pkgrel)"
  [[ "$old_version" =~ $version_pattern ]] || { echo "Invalid remote AUR version" >&2; exit 1; }
  if cmp -s PKGBUILD "$bundle/PKGBUILD" && cmp -s .SRCINFO "$bundle/aur.SRCINFO"; then
    echo "AUR already matches; nothing to push."
    exit 0
  fi
  if dpkg --compare-versions "$old_version" ge "$new_version"; then
    echo "Refusing an AUR downgrade or conflicting same-version packaging." >&2
    exit 1
  fi
fi
cp "$bundle/PKGBUILD" PKGBUILD
cp "$bundle/aur.SRCINFO" .SRCINFO
git config user.name "qrcode-pretty release"
git config user.email "qrcode-pretty-release@users.noreply.github.com"
git add -- PKGBUILD .SRCINFO
git commit -m "Update qrcode-pretty to $new_version"
# Normal fast-forward push; concurrent remote edits fail rather than being lost.
git push origin HEAD:master
echo "AUR updated to $new_version."
