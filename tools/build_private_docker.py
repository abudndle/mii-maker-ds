#!/usr/bin/env python3
"""Build your private Mii Maker DS ROM using the official BlocksDS Docker SDK.

No original files are committed, sent to GitHub Actions or uploaded. The
private archive is mounted read-only inside the temporary container.
Docker must already be installed locally and its official image available.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "skylyrac/blocksds:slim-latest"


def command(archive, root=ROOT, image=IMAGE, jobs=2, validate_only=False, environ=None):
    env = os.environ if environ is None else environ
    root = Path(root).resolve(strict=True)
    archive = Path(archive).expanduser().resolve(strict=True)
    if not archive.is_file() or archive.stat().st_size <= 0:
        raise ValueError("private ZIP does not exist or is empty")
    if not 1 <= jobs <= 16:
        raise ValueError("jobs must be between 1 and 16")
    if not image or any(ch.isspace() for ch in image) or image.startswith("-"):
        raise ValueError("invalid Docker image identifier")
    # Avoid accidental Docker mount aliasing that would conceal the workspace.
    if root == archive or root == archive.parent:
        raise ValueError("keep private resource ZIP separate from project root")
    args = [
        "docker", "run", "--rm", "--network", "none",
        "--security-opt", "no-new-privileges", "--cap-drop", "ALL",
        "--workdir", "/work",
        "--mount", f"type=bind,source={root},target=/work",
        "--mount", f"type=bind,source={archive},target=/private/resources.zip,readonly",
    ]
    if hasattr(os, "getuid") and env.get("MDS_DOCKER_RUN_AS_ROOT") != "1":
        args += ["--user", f"{os.getuid()}:{os.getgid()}"]
    args += [image, "python3", "tools/build_private.py", "/private/resources.zip"]
    if validate_only:
        args.append("--validate-only")
    else:
        args.extend(["--jobs", str(jobs)])
    return args


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_zip", type=Path)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--image", default=IMAGE)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="show command without running Docker or accessing asset bytes")
    args = parser.parse_args()
    try:
        cmd = command(args.private_zip, image=args.image, jobs=args.jobs,
                      validate_only=args.validate_only)
        if args.dry_run:
            print("Docker private build invocation prepared (resource ZIP is mounted read-only).")
            print(" ".join(shlex_quote(part) for part in cmd))
            return 0
        if shutil.which("docker") is None:
            raise ValueError("Docker is not installed; see the official BlocksDS Docker setup")
        subprocess.run(cmd, check=True, cwd=ROOT)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"FAIL: private BlocksDS Docker build: {exc}\n")
    if not args.validate_only:
        print("Local ROM candidate: mii-ds.nds; keep it private.")
        print("All private build-time ROM gates were run inside the container.")
    return 0


def shlex_quote(item):
    # Display only: direct subprocess.run is used, never a shell.
    import shlex
    return shlex.quote(str(item))


if __name__ == "__main__":
    raise SystemExit(main())
