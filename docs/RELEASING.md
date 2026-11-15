# Coordinated releases

## Supported delivery channels

The release workflow publishes Python distributions to PyPI, pushes packaging to
`ssh://aur@aur.archlinux.org/qrcode-pretty.git`, and publishes a GitHub Release
with wheel, sdist, Debian 13 and Ubuntu 24.04 packages, build records, checksums,
and a source/artifact manifest. Nix consumers use the source tag and update their
own flake locks; there is no separate Nix registry publication.

Debian/Ubuntu delivery is downloadable `.deb` files, **not an APT repository or
PPA**. Support applies to the tested distribution versions; `Architecture: all`
does not certify other distributions.

## One-time maintainer setup

1. Enable GitHub Actions and permit workflows to create pull requests. The
   preparation job requests contents-write and pull-requests-write permissions.
2. Protect `main`: require review and successful CI (including the package
   matrix) before merging. Merge release PRs using **merge or squash**, not a
   rebase-only strategy: release detection matches the PR's merge commit.
3. Create/protect the GitHub environment named `release`. Require a reviewer;
   optionally prevent self-review. Confirm environment-reviewer support for
   your repository visibility and GitHub plan. Restrict deployment branches to
   `main`. Without these settings, YAML alone does not enforce human approval.
4. Keep/configure PyPI Trusted Publishing for this repository, workflow filename
   `release.yaml`, and environment `release`. No PyPI API token is needed.
5. In that environment, configure:
   - `AUR_SSH_PRIVATE_KEY`: multiline private key for a dedicated AUR publisher.
     Upload the corresponding public key to an AUR account permitted to update
     this package. A dedicated co-maintainer/service account limits exposure.
   - `AUR_KNOWN_HOSTS`: a verified OpenSSH known_hosts entry for
     `aur.archlinux.org`. Verify the host fingerprint out-of-band using Arch's
     official information before storing it. Do not blindly trust runtime
     `ssh-keyscan` output. No key is embedded in this repository.
6. Protect stable release tags from movement/deletion. If tag creation is
   restricted by a ruleset, explicitly authorize the intended workflow actor
   without granting broad bypass rights.
7. Optional: configure separate `test-release` environment protection and a
   TestPyPI trusted publisher for `test-release.yaml`.

Actions are pinned to commit SHAs; uv is pinned. Container tags are resolved to
image IDs once per job. Resolved registry digests are saved in runner-owned
`*-image.json` files; installed package versions are recorded separately in
container-created `*-build.txt` files. Keeping them separate avoids host writes
to Docker's root-owned output files. Apt/pacman packages can change between builds; this is
**not** a claim of bit-for-bit reproducibility. Pin/update base-image digests and
package snapshots separately if archival reproducibility becomes a requirement.

## Normal release

1. Run **Prepare release** from `main`, supplying a new bare stable version
   such as `1.2.0`. Do not enter a `v` prefix. Prereleases are not currently
   supported by this coordinated pipeline.
2. The workflow updates pyproject, uv.lock, PKGBUILD and Debian changelog, tests
   the result, pushes `release/X.Y.Z`, and opens a PR. Existing release branches
   are never force-updated; inspect the existing PR before repeating preparation.
3. Review the PR. GitHub may require a maintainer to approve workflow runs for
   PRs opened using GITHUB_TOKEN. The preparation job runs unit tests, but
   **also ensure the PR package-matrix CI runs and passes** before merging.
4. Merge the PR. A regular push without a version change does not publish.
   Changed upstream versions must originate from a matching same-repository,
   merged preparation PR. Required branch checks/review are enforced through
   the repository settings above, not inferred from labels.
5. Release validates/tests the merge SHA, creates/verifies its immutable bare
   tag, then builds all channels at that SHA. The real Arch recipe fetches the
   tag and verifies the resulting source commit. PR builds use a temporary
   local-source override because the future release tag does not yet exist.
6. Inspect the build results, then approve the single `release` environment job.
   Tag creation happens **before** this approval so Arch can test the actual
   recipe. Package publication happens only after approval.
7. The publisher verifies the original artifact manifest, stages GitHub draft
   assets, publishes PyPI, pushes AUR, and makes the GitHub Release public. The
   Actions summary reports each channel.

The coordinator calls the build workflow directly: it does not depend on a
GITHUB_TOKEN-created tag triggering a second workflow. The single publisher job
means one environment approval, but job-level contents-write/OIDC capability is
shared across its steps. Build jobs receive neither publication secrets nor
write permissions; the AUR key is passed only to the AUR step. No package build
scripts execute in the publisher.

## Retry and partial-publication recovery

Registries cannot participate in one transaction. PyPI or AUR may be published
even if a later step fails and the GitHub release remains a draft.

- **Before a bundle exists:** rerun the original failed build/run at the same
  source SHA. A transient workflow/build failure does not require a version bump.
  If source changes are needed, stop and review the release state; automation
  never moves the reserved tag or republishes changed bytes.
- **Once any channel may have published:** preserve and reuse the original
  `release-bundle`. Run **Release** manually from `main`, providing its bare
  version and the original completed Release workflow run ID. Recovery verifies
  the producing repository, workflow, event, SHA, manifest identity and checksums.
  It skips rebuilding/tagging and still requires the protected approval.
- Existing identical PyPI files are skipped by pinned uv. Differing bytes fail.
  Existing GitHub assets are downloaded and compared; nothing is overwritten.
- AUR is a no-op if both packaging files match. A same-version packaging conflict
  or newer remote version fails; pushes are ordinary fast-forward pushes, never
  forced. AUR packaging-only revisions need an explicit separate maintenance
  change; don't republish PyPI just to change pkgrel.
- Do not rerun all build jobs after partial publication and expect regenerated
  artifacts to match. Prefer the recovery dispatch with the original run ID.
- Bundles and build artifacts have **90-day Actions retention** (subject to
  repository/organization limits). Draft/public GitHub assets also retain the
  bundle's files once staging succeeds, but automated recovery currently reads
  the original Actions artifact. Preserve it externally before expiry if needed.
  If it has expired or original missing files are lost, stop for manual recovery;
  do not silently rebuild or overwrite existing releases.
- Release 1.1.1 predates this pipeline and has no compatible bundle. Do not move
  its tag or use it as a live publication test.

Publication is serialized per version. Keep unrelated release preparations
sequential; do not merge another version until the previous one is resolved.

## Test and verification workflows

- CI runs actionlint/ShellCheck, tests Python 3.10/3.12/3.13 and runs the
  reusable Python, Debian, Ubuntu and Arch build/install checks.
- Debian builds use distro Build-Depends, pybuild/pytest and Lintian; fresh
  runtime containers install via apt and run CLI/image/asset checks as a regular
  user, then purge the package. Lintian errors fail the build; the current
  `no-manual-page` warning is accepted because the CLI provides `--help` but no
  packaged man page yet.
- Arch uses unprivileged makepkg, install/runtime/remove checks, and atomic
  .SRCINFO generation. Only its two validated packaging files are pushed to AUR.
- The **Test release** manual workflow reuses the same build validation and
  publishes only Python artifacts to TestPyPI. It never pushes AUR or GitHub
  releases. TestPyPI versions/files are immutable too: changed bytes under a
  previously uploaded version must fail. Use a genuinely unused test version or
  inspect CI artifacts without publishing.
- Python wheel and sdist are installed in separate fresh environments and smoke
  tested away from the source checkout, including the bundled default image.

Local non-publishing checks (Python >= 3.11 for release scripts):

```sh
uv sync --locked
uv run --locked pytest
python3 scripts/release/release.py validate
actionlint
shellcheck scripts/release/*.sh
git diff --check
```

Preparation helper (in a clean disposable branch; this changes metadata locally):

```sh
python3 scripts/release/release.py prepare 1.2.0 \
  --name 'Release maintainer' --email 'maintainer@example.invalid'
```

Choose the real next release version and changelog identity; the example is not
an instruction to bump the existing published release.

For full non-publishing local checks of your working tree:

```sh
bash scripts/release/check-containers.sh deb13
bash scripts/release/check-containers.sh ubuntu24.04
bash scripts/release/check-containers.sh arch
```

The helper defaults to Docker; set `CONTAINER_ENGINE=podman` for an already
configured rootless Podman environment. On Linux, also set `PODMAN_KEEP_ID=true`
to run the container as root while mapping your host UID to a non-root container
UID. This exposes ownership problems that rootless Podman's default mapping can
hide, including preserved source ownership and unwritable container output files.
The helper copies tracked/unignored files into containers and deletes temporary
build outputs after testing. The workflow uses
its own exact-commit archive rather than a developer working tree.

Do not run build-deb.sh, test-deb.sh or build-arch.sh directly on your host: those
scripts install packages and create users inside their disposable container.
