#!/usr/bin/env python3
"""Stage immutable release assets, then expose the completed release."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

from release import checksum, run, stable


def stage(directory, version, sha):
    repo = os.environ["GITHUB_REPOSITORY"]
    # Use status, not a blanket exception: authentication/server failures are fatal.
    result = subprocess.run(["gh", "api", f"repos/{repo}/releases/tags/{version}"],
                            text=True, capture_output=True)
    if result.returncode:
        if "HTTP 404" not in result.stderr:
            raise RuntimeError(result.stderr)
        run("gh", "release", "create", version, "--verify-tag", "--draft",
            "--title", version, "--notes",
            f"Release {version}\n\nSource commit: {sha}\n\nDebian 13 and Ubuntu 24.04 packages are provided as downloads, not an APT repository.")
        release = json.loads(run("gh", "api", f"repos/{repo}/releases/tags/{version}"))
    else:
        release = json.loads(result.stdout)
    if release["tag_name"] != version:
        raise ValueError("Release tag mismatch")
    # Don't overwrite assets, including on recovery after public release.
    assets = json.loads(run("gh", "api", "--paginate", "--slurp",
                           f"repos/{repo}/releases/{release['id']}/assets?per_page=100"))
    assets = [a for page in assets for a in page]
    local = {p.name: p for p in directory.iterdir()}
    with tempfile.TemporaryDirectory() as tmp:
        for asset in assets:
            name = asset["name"]
            if name not in local:
                raise ValueError(f"Unexpected existing release asset: {name}")
            path = Path(tmp) / name
            with path.open("wb") as stream:
                subprocess.run(["gh", "api", "-H", "Accept: application/octet-stream",
                                f"repos/{repo}/releases/assets/{asset['id']}"], stdout=stream, check=True)
            if checksum(path) != checksum(local[name]):
                raise ValueError(f"Existing GitHub asset has different bytes: {name}")
        existing = {a["name"] for a in assets}
        for name in sorted(local.keys() - existing):
            run("gh", "release", "upload", version, str(local[name]))
    print("GitHub assets match the original bundle.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["stage", "finish"])
    parser.add_argument("directory", type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--sha", required=True)
    args = parser.parse_args()
    stable(args.version)
    if run("git", "rev-parse", f"refs/tags/{args.version}^{{commit}}") != args.sha:
        raise ValueError("Tag changed since build")
    if args.command == "stage":
        stage(args.directory, args.version, args.sha)
    else:
        run("gh", "release", "edit", args.version, "--draft=false")
        print("GitHub Release is public.")


if __name__ == "__main__":
    main()
