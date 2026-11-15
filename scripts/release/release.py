#!/usr/bin/env python3
"""Release metadata, identity, and artifact validation (Python >= 3.11)."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tomllib

STABLE = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")
ROOT = Path(__file__).resolve().parents[2]


def run(*args, cwd=None):
    return subprocess.check_output(args, cwd=cwd or ROOT, text=True).strip()


def stable(version):
    if not STABLE.fullmatch(version):
        raise ValueError("Expected a bare stable X.Y.Z version (no v prefix)")
    return version


def project_version(root=ROOT):
    return tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]


def validate(root=ROOT, version=None):
    version = stable(version or project_version(root))
    if project_version(root) != version:
        raise ValueError("Tag/version differs from pyproject.toml")
    lock = tomllib.loads((root / "uv.lock").read_text())
    locked = [p["version"] for p in lock["package"] if p["name"] == "qrcode-pretty"]
    if locked != [version]:
        raise ValueError("uv.lock project version differs")
    recipe = (root / "PKGBUILD").read_text()
    if not re.search(rf"^pkgver={re.escape(version)}$", recipe, re.M):
        raise ValueError("PKGBUILD version differs")
    if not re.search(r"^pkgrel=[1-9][0-9]*$", recipe, re.M):
        raise ValueError("Invalid AUR pkgrel")
    first = (root / "debian/changelog").read_text().splitlines()[0]
    if not re.fullmatch(rf"qrcode-pretty \({re.escape(version)}-[1-9][0-9]*\) unstable; urgency=\w+", first):
        raise ValueError("Debian changelog upstream version/revision differs")
    return version


def prepare(root, version, name, email, now=None):
    stable(version)
    old = stable(project_version(root))
    if tuple(map(int, version.split("."))) <= tuple(map(int, old.split("."))):
        raise ValueError("Preparation requires a newer upstream version; use recovery for retries")
    if not name.strip() or not email.strip() or any(c in name + email for c in "\r\n"):
        raise ValueError("Invalid changelog identity")
    project = root / "pyproject.toml"
    project.write_text(project.read_text().replace(f'version = "{old}"', f'version = "{version}"', 1))
    recipe = root / "PKGBUILD"
    text = re.sub(r"^pkgver=.*$", f"pkgver={version}", recipe.read_text(), flags=re.M)
    recipe.write_text(re.sub(r"^pkgrel=.*$", "pkgrel=1", text, flags=re.M))
    changelog = root / "debian/changelog"
    date = (now or dt.datetime.now(dt.timezone.utc)).strftime("%a, %d %b %Y %H:%M:%S +0000")
    entry = f"qrcode-pretty ({version}-1) unstable; urgency=medium\n\n  * New upstream release {version}.\n\n -- {name} <{email}>  {date}\n\n"
    changelog.write_text(entry + changelog.read_text())
    # uv owns its lock format; do not patch it by text substitution.
    run("uv", "lock", cwd=root)
    validate(root, version)


def output(**values):
    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with open(target, "a") as stream:
            for key, value in values.items():
                if "\n" in str(value):
                    raise ValueError("Invalid workflow output")
                stream.write(f"{key}={value}\n")
    else:
        print(json.dumps(values, indent=2))


def api(path):
    return json.loads(run("gh", "api", path))


def resolve():
    """Only a merged, same-repository preparation PR may initiate publication."""
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    repo = os.environ["GITHUB_REPOSITORY"]
    if os.environ["GITHUB_EVENT_NAME"] == "workflow_dispatch":
        if os.environ["GITHUB_REF"] != "refs/heads/main":
            raise ValueError("Recovery must run from main")
        version = stable(event["inputs"]["version"])
        artifact_run = event["inputs"]["artifact_run"]
        if not re.fullmatch(r"[1-9][0-9]*", artifact_run):
            raise ValueError("Recovery requires the original release run ID")
        sha = run("git", "rev-parse", f"refs/tags/{version}^{{commit}}")
        original = api(f"repos/{repo}/actions/runs/{artifact_run}")
        if not (original["head_sha"] == sha and original["event"] == "push"
                and original["path"] == ".github/workflows/release.yaml"
                and original["repository"]["full_name"] == repo
                and original["status"] == "completed"):
            raise ValueError("Not a completed original release run for this tagged commit")
        run("git", "checkout", "--detach", sha)
        validate(ROOT, version)
        output(release="true", version=version, sha=sha, artifact_run=artifact_run)
        return
    sha = os.environ["GITHUB_SHA"]
    version = validate()
    before = event["before"]
    if set(before) == {"0"}:
        raise ValueError("Ref creation is not a release merge")
    previous = tomllib.loads(run("git", "show", f"{before}:pyproject.toml"))["project"]["version"]
    if previous == version:
        output(release="false")
        return
    if tuple(map(int, version.split("."))) <= tuple(map(int, stable(previous).split("."))):
        raise ValueError("Upstream version must increase")
    prs = api(f"repos/{repo}/commits/{sha}/pulls")
    matches = [p for p in prs if p.get("merged_at") and p["merge_commit_sha"] == sha
               and p["base"]["ref"] == "main" and p["base"]["repo"]["full_name"] == repo
               and p["head"].get("repo") and p["head"]["repo"]["full_name"] == repo
               and p["head"]["ref"] == f"release/{version}"]
    if len(matches) != 1:
        raise ValueError("Version changes must be merged via the release-preparation PR")
    output(release="true", version=version, sha=sha, artifact_run=os.environ["GITHUB_RUN_ID"])


def checksum(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def manifest(directory, version, sha, run_id):
    stable(version)
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Expected full commit SHA")
    paths = sorted(p for p in directory.iterdir() if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS"})
    names = {p.name for p in paths}
    required = {f"qrcode_pretty-{version}-py3-none-any.whl", f"qrcode_pretty-{version}.tar.gz",
                f"qrcode-pretty_{version}-1+deb13_all.deb", f"qrcode-pretty_{version}-1+ubuntu24.04_all.deb",
                "PKGBUILD", "aur.SRCINFO", "deb13-build.txt", "ubuntu24.04-build.txt", "arch-build.txt",
                "deb13-image.json", "ubuntu24.04-image.json", "arch-image.json"}
    if not required <= names or any(p.is_symlink() for p in paths):
        raise ValueError(f"Missing/unsafe release artifacts: {required - names}")
    data = {"version": version, "sha": sha, "run_id": str(run_id),
            "files": {p.name: checksum(p) for p in paths}}
    (directory / "manifest.json").write_text(json.dumps(data, indent=2) + "\n")
    sums = dict(data["files"], **{"manifest.json": checksum(directory / "manifest.json")})
    (directory / "SHA256SUMS").write_text("".join(f"{digest}  {name}\n" for name, digest in sorted(sums.items())))


def verify(directory, version, sha, run_id):
    data = json.loads((directory / "manifest.json").read_text())
    if (data["version"], data["sha"], data["run_id"]) != (stable(version), sha, str(run_id)):
        raise ValueError("Artifact identity does not match version, commit and original run")
    expected = set(data["files"]) | {"manifest.json", "SHA256SUMS"}
    if {p.name for p in directory.iterdir()} != expected:
        raise ValueError("Unexpected or missing bundle files")
    for name, digest in data["files"].items():
        path = directory / name
        if Path(name).name != name or path.is_symlink() or not path.is_file() or checksum(path) != digest:
            raise ValueError(f"Artifact checksum/path conflict: {name}")
    expected_sums = dict(data["files"], **{"manifest.json": checksum(directory / "manifest.json")})
    sums = "".join(f"{digest}  {name}\n" for name, digest in sorted(expected_sums.items()))
    if (directory / "SHA256SUMS").read_text() != sums:
        raise ValueError("SHA256SUMS differs from manifest")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("version")
    p.add_argument("--name", required=True)
    p.add_argument("--email", required=True)
    p = sub.add_parser("validate")
    p.add_argument("--version")
    sub.add_parser("resolve")
    for cmd in ("manifest", "verify"):
        p = sub.add_parser(cmd)
        p.add_argument("directory", type=Path)
        p.add_argument("--version", required=True)
        p.add_argument("--sha", required=True)
        p.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(ROOT, args.version, args.name, args.email)
    elif args.command == "validate":
        print(validate(version=args.version))
    elif args.command == "resolve":
        resolve()
    else:
        globals()[args.command](args.directory, args.version, args.sha, args.run_id)


if __name__ == "__main__":
    main()
