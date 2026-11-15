"""Non-publishing tests for release preparation, provenance and recovery."""
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

pytest.importorskip("tomllib", reason="Release tooling runs on Python >= 3.11")
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts/release"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("release", SCRIPTS / "release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
import github_release  # noqa: E402

VERSION = "1.2.0"
SHA = "a" * 40
RUN = "123"


@pytest.fixture
def metadata(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "1.1.1"\n')
    (tmp_path / "uv.lock").write_text('[[package]]\nname = "qrcode-pretty"\nversion = "1.1.1"\n')
    (tmp_path / "PKGBUILD").write_text("pkgver=1.1.1\npkgrel=2\n")
    (tmp_path / "debian").mkdir()
    (tmp_path / "debian/changelog").write_text("qrcode-pretty (1.1.1-1) unstable; urgency=medium\n\n  * Historical entry.\n")
    return tmp_path


@pytest.mark.parametrize("version", ["v1.2.0", "1.2", "1.2.0rc1", "01.2.0", "1.2.0\n", "1.2.0;echo bad"])
def test_version_rejects_unsafe_or_nonstable_input(version):
    with pytest.raises(ValueError):
        release.stable(version)


def test_preparation_synchronizes_and_preserves_history(metadata, monkeypatch):
    def fake_uv(*args, cwd):
        assert args == ("uv", "lock")
        (cwd / "uv.lock").write_text(f'[[package]]\nname = "qrcode-pretty"\nversion = "{VERSION}"\n')
    monkeypatch.setattr(release, "run", fake_uv)
    release.prepare(metadata, VERSION, "Release", "release@example.invalid", dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc))
    assert release.validate(metadata, VERSION) == VERSION
    assert "pkgrel=1\n" in (metadata / "PKGBUILD").read_text()
    assert "Historical entry" in (metadata / "debian/changelog").read_text()
    assert "01 Jan 2026" in (metadata / "debian/changelog").read_text()


@pytest.mark.parametrize("version", ["1.1.1", "1.0.0"])
def test_preparation_cannot_repurpose_existing_version(metadata, version):
    with pytest.raises(ValueError):
        release.prepare(metadata, version, "Release", "release@example.invalid")


@pytest.mark.parametrize("file", ["pyproject.toml", "uv.lock", "PKGBUILD", "debian/changelog"])
def test_validation_rejects_scattered_metadata(metadata, file):
    path = metadata / file
    path.write_text(path.read_text().replace("1.1.1", "1.1.0"))
    with pytest.raises(ValueError):
        release.validate(metadata, "1.1.1")


@pytest.fixture
def bundle(tmp_path):
    names = [f"qrcode_pretty-{VERSION}-py3-none-any.whl", f"qrcode_pretty-{VERSION}.tar.gz",
             f"qrcode-pretty_{VERSION}-1+deb13_all.deb", f"qrcode-pretty_{VERSION}-1+ubuntu24.04_all.deb",
             "PKGBUILD", "aur.SRCINFO", "deb13-build.txt", "ubuntu24.04-build.txt", "arch-build.txt",
             "deb13-image.json", "ubuntu24.04-image.json", "arch-image.json"]
    for name in names:
        (tmp_path / name).write_text(f"Original artifact: {name}")
    return tmp_path


def seal(bundle):
    release.manifest(bundle, VERSION, SHA, RUN)


def test_bundle_verifies_identity_and_content(bundle):
    seal(bundle)
    assert release.verify(bundle, VERSION, SHA, RUN)["sha"] == SHA
    assert "manifest.json" in (bundle / "SHA256SUMS").read_text()


@pytest.mark.parametrize("change", ["checksum", "missing", "extra", "sums", "symlink"])
def test_bundle_rejects_changed_or_unsafe_files(bundle, change):
    seal(bundle)
    if change == "checksum":
        (bundle / "PKGBUILD").write_text("rebuilt bytes")
    elif change == "missing":
        (bundle / "PKGBUILD").unlink()
    elif change == "extra":
        (bundle / "unexpected").write_text("not in manifest")
    elif change == "sums":
        (bundle / "SHA256SUMS").write_text("modified")
    else:
        (bundle / "PKGBUILD").unlink()
        (bundle / "PKGBUILD").symlink_to(bundle / "aur.SRCINFO")
    with pytest.raises(ValueError):
        release.verify(bundle, VERSION, SHA, RUN)


@pytest.mark.parametrize("version,sha,run", [("1.2.1", SHA, RUN), (VERSION, "b" * 40, RUN), (VERSION, SHA, "456")])
def test_bundle_rejects_wrong_release_identity(bundle, version, sha, run):
    seal(bundle)
    with pytest.raises(ValueError):
        release.verify(bundle, version, sha, run)


@pytest.mark.parametrize("missing", [f"qrcode-pretty_{VERSION}-1+deb13_all.deb",
                                     "deb13-image.json", "ubuntu24.04-image.json", "arch-image.json"])
def test_manifest_requires_every_distribution_and_provenance(bundle, missing):
    (bundle / missing).unlink()
    with pytest.raises(ValueError):
        seal(bundle)


@pytest.fixture
def event_env(tmp_path, monkeypatch):
    event = tmp_path / "event.json"
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event))
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/qrcode-pretty")
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_SHA", SHA)
    monkeypatch.setenv("GITHUB_RUN_ID", RUN)
    return event


def test_resolve_ordinary_commit_does_not_release(event_env, monkeypatch):
    event_env.write_text(json.dumps({"before": "b" * 40}))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setattr(release, "validate", lambda: VERSION)
    monkeypatch.setattr(release, "run", lambda *a: f'[project]\nversion = "{VERSION}"')
    values = {}
    monkeypatch.setattr(release, "output", lambda **kw: values.update(kw))
    release.resolve()
    assert values == {"release": "false"}


@pytest.mark.parametrize("valid_pr", [True, False])
def test_only_matching_merged_release_pr_initiates_release(event_env, monkeypatch, valid_pr):
    event_env.write_text(json.dumps({"before": "b" * 40}))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setattr(release, "validate", lambda: VERSION)
    monkeypatch.setattr(release, "run", lambda *a: '[project]\nversion = "1.1.1"')
    pr = {"merged_at": "2026-01-01", "merge_commit_sha": SHA,
          "base": {"ref": "main", "repo": {"full_name": "owner/qrcode-pretty"}},
          "head": {"ref": f"release/{VERSION}", "repo": {"full_name": "owner/qrcode-pretty" if valid_pr else "fork/qrcode-pretty"}}}
    monkeypatch.setattr(release, "api", lambda path: [pr])
    values = {}
    monkeypatch.setattr(release, "output", lambda **kw: values.update(kw))
    if valid_pr:
        release.resolve()
        assert values == {"release": "true", "version": VERSION, "sha": SHA, "artifact_run": RUN}
    else:
        with pytest.raises(ValueError):
            release.resolve()


@pytest.mark.parametrize("mutation", [None, "head_sha", "event", "path", "status"])
def test_recovery_requires_original_completed_release_run(event_env, monkeypatch, mutation):
    event_env.write_text(json.dumps({"inputs": {"version": VERSION, "artifact_run": RUN}}))
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    original = {"head_sha": SHA, "event": "push", "path": ".github/workflows/release.yaml",
                "status": "completed", "repository": {"full_name": "owner/qrcode-pretty"}}
    if mutation:
        original[mutation] = "invalid"
    monkeypatch.setattr(release, "api", lambda path: original)
    monkeypatch.setattr(release, "run", lambda *a: SHA)
    monkeypatch.setattr(release, "validate", lambda *a: VERSION)
    values = {}
    monkeypatch.setattr(release, "output", lambda **kw: values.update(kw))
    if mutation:
        with pytest.raises(ValueError):
            release.resolve()
    else:
        release.resolve()
        assert values["artifact_run"] == RUN


@pytest.mark.parametrize("target", ["deb13", "ubuntu24.04", "arch"])
def test_container_helper_does_not_append_to_container_owned_records(tmp_path, target):
    """An unwritable build record reproduces the host-side Docker failure."""
    root = tmp_path / "repo"
    scripts = root / "scripts/release"
    scripts.mkdir(parents=True)
    helper = scripts / "check-containers.sh"
    helper.write_text((SCRIPTS / helper.name).read_text())
    (root / "README.md").write_text("test source")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    git = bin_dir / "git"
    git.write_text('#!/usr/bin/env bash\ncase "$1" in\n'
                   'ls-files) printf "README.md\\0" ;;\n'
                   'show) echo 1 ;;\n*) exit 99 ;;\nesac\n')
    git.chmod(0o755)
    engine = bin_dir / "engine"
    engine.write_text('''#!/usr/bin/env python3
import os
from pathlib import Path
import sys
args = sys.argv[1:]
if args[0] == "pull":
    pass
elif args[:2] == ["image", "inspect"]:
    print('["image@sha256:test"]' if "RepoDigests" in args[3] else "sha256:test")
elif args[0] == "run":
    for value in args:
        if value.endswith(":/out"):
            directory = Path(value[:-5])
            record = directory / (os.environ["FAKE_TARGET"] + "-build.txt")
            record.write_text("container-owned build record")
            record.chmod(0o444)
else:
    sys.exit(99)
''')
    engine.chmod(0o755)
    result = subprocess.run(["bash", str(helper), target], capture_output=True, text=True,
                            env={**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}",
                                 "CONTAINER_ENGINE": str(engine), "PODMAN_KEEP_ID": "false", "FAKE_TARGET": target})
    assert result.returncode == 0, result.stderr
    assert f"checks passed: {target}" in result.stdout


def test_github_errors_are_not_treated_as_missing_release(bundle, monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/qrcode-pretty")
    monkeypatch.setattr(github_release.subprocess, "run", lambda *a, **kw: subprocess.CompletedProcess(a, 1, "", "HTTP 403"))
    with pytest.raises(RuntimeError, match="403"):
        github_release.stage(bundle, VERSION, SHA)


def test_github_conflicting_asset_is_never_overwritten(bundle, monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/qrcode-pretty")
    def fake_run(*args, **kwargs):
        if "stdout" in kwargs:
            kwargs["stdout"].write(b"different published bytes")
            return subprocess.CompletedProcess(args, 0)
        return subprocess.CompletedProcess(args, 0, json.dumps({"tag_name": VERSION, "id": 42}), "")
    monkeypatch.setattr(github_release.subprocess, "run", fake_run)
    monkeypatch.setattr(github_release, "run", lambda *a: json.dumps([[{"name": "PKGBUILD", "id": 7}]]))
    with pytest.raises(ValueError, match="different bytes"):
        github_release.stage(bundle, VERSION, SHA)


@pytest.mark.parametrize("state,expected,push", [
    ("identical", 0, False), ("older", 0, True),
    ("conflict", 1, False), ("newer", 1, False), ("invalid", 1, False),
])
def test_aur_push_is_idempotent_and_never_downgrades(tmp_path, state, expected, push):
    """All git/dpkg operations are stubs: no actual remote access or push."""
    bundle = tmp_path / "bundle"
    remote = tmp_path / "remote"
    bin_dir = tmp_path / "bin"
    for path in (bundle, remote, bin_dir):
        path.mkdir()
    (bundle / "PKGBUILD").write_text("pkgver=1.2.0\npkgrel=1\n")
    info = "pkgver = 1.2.0\npkgrel = 1\n"
    (bundle / "aur.SRCINFO").write_text(info)
    (remote / "PKGBUILD").write_text((bundle / "PKGBUILD").read_text() if state == "identical" else "different recipe\n")
    old = {"older": "1.1.1", "newer": "1.3.0", "invalid": "broken"}.get(state, "1.2.0")
    (remote / ".SRCINFO").write_text(info.replace("1.2.0", old))
    git = bin_dir / "git"
    git.write_text('#!/usr/bin/env bash\nset -eu\ncase "$1" in\n'
                   'clone) mkdir -p "$3"; cp "$FAKE_REMOTE/PKGBUILD" "$3/PKGBUILD"; cp "$FAKE_REMOTE/.SRCINFO" "$3/.SRCINFO" ;;\n'
                   'push) printf "%s\\n" "$*" > "$FAKE_PUSH_LOG" ;;\n'
                   'config|add|commit) : ;;\n*) exit 99 ;;\nesac\n')
    git.chmod(0o755)
    dpkg = bin_dir / "dpkg"
    dpkg.write_text('#!/usr/bin/env bash\n[[ "$FAKE_REMOTE_STATE" != older ]]\n')
    dpkg.chmod(0o755)
    log = tmp_path / "push.log"
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}",
           "AUR_SSH_PRIVATE_KEY": "not-a-real-private-key",
           "AUR_KNOWN_HOSTS": "not-a-real-host-key", "FAKE_REMOTE": str(remote),
           "FAKE_PUSH_LOG": str(log), "FAKE_REMOTE_STATE": state}
    result = subprocess.run(["bash", str(SCRIPTS / "publish-aur.sh"), str(bundle)],
                            env=env, capture_output=True, text=True)
    assert result.returncode == expected, result.stderr
    assert log.exists() is push
    if push:
        assert log.read_text().strip() == "push origin HEAD:master"
