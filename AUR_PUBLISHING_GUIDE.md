# Publishing qrcode-pretty to AUR

Normal upstream releases are automated through a release-preparation PR and one
protected approval. The pipeline **pushes** `PKGBUILD` and generated `.SRCINFO`
to:

```text
ssh://aur@aur.archlinux.org/qrcode-pretty.git
```

See [Coordinated releases](docs/RELEASING.md) for the complete process, secret
setup, required GitHub protections, and safe partial-release recovery.

## Pipeline behavior

- Update pkgver/pkgrel with the other metadata in the preparation PR.
- Test PR packaging in Arch using a temporary source override.
- After merge, create the immutable upstream tag, build the real tag-pinned
  recipe in Arch, verify its source SHA, install/test/remove the package.
- Generate `.SRCINFO` as an unprivileged user with a real makepkg configuration,
  using temporary output plus atomic rename.
- After approval and PyPI publication, clone the AUR repository using a dedicated
  SSH key and verified host key, copy the validated files, commit and push.
- Exact matching files are a successful no-op. Same-version conflicts, downgrades
  and non-fast-forward pushes fail rather than overwriting remote changes.

Required `release` environment secrets: `AUR_SSH_PRIVATE_KEY` and
`AUR_KNOWN_HOSTS`. Never commit either secret or disable SSH host verification.

## Manual packaging maintenance

Packaging-only fixes such as a pkgrel increment are separate from upstream
releases. Review current remote packaging before making such changes. Use a
real Arch environment for makepkg, not an incomplete NixOS installation.

In the AUR checkout, after reviewing/updating PKGBUILD:

```sh
makepkg --cleanbuild
makepkg --printsrcinfo > .SRCINFO.tmp &&
  test -s .SRCINFO.tmp &&
  mv .SRCINFO.tmp .SRCINFO
git diff --check
git diff -- PKGBUILD .SRCINFO
```

A maintainer can then commit and push the reviewed files. Keep this repository's
PKGBUILD aligned with deliberate packaging changes; automatic release recovery
will not overwrite a conflicting same-version AUR update.
