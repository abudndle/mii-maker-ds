#!/usr/bin/env python3
"""Verify the *running* melonDS 1.1 Qt process uses the prepared DS B mapping.

This private-safe diagnostic never prints the emulator executable, HOME,
configuration paths, or the owner ROM. It follows melonDS 1.1 pathInit():
a portable directory next to the executable wins over QStandardPaths.
"""
import argparse
import os
from pathlib import Path
import tomllib


def inspect(pid: int, expected_home: Path, proc_root: Path = Path("/proc")) -> str:
    if pid <= 0:
        raise ValueError("invalid emulator PID")
    proc = proc_root / str(pid)
    raw = (proc / "environ").read_bytes()
    env = {}
    for entry in raw.split(b"\0"):
        if b"=" in entry:
            key, value = entry.split(b"=", 1)
            if key in (b"HOME", b"XDG_CONFIG_HOME"):
                env[key.decode()] = os.fsdecode(value)
    home = env.get("HOME")
    if not home or Path(home).resolve() != expected_home.resolve():
        raise ValueError("emulator HOME does not match isolated runner HOME")

    exe = Path(os.readlink(proc / "exe"))
    if (exe.parent / "portable").is_dir():
        raise ValueError("emulator uses executable-adjacent portable config")
    xdg = env.get("XDG_CONFIG_HOME")
    config_root = Path(xdg) if xdg else Path(home) / ".config"
    expected_root = expected_home / ".config"
    if config_root.resolve() != expected_root.resolve():
        raise ValueError("emulator XDG config root overrides isolated HOME")
    config = config_root / "melonDS" / "melonDS.toml"
    if not config.is_file():
        raise ValueError("emulator's effective TOML is absent")
    try:
        parsed = tomllib.loads(config.read_text(encoding="utf-8"))
        b = parsed["Instance0"]["Keyboard"]["B"]
    except (OSError, UnicodeError, tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
        raise ValueError("emulator's effective B mapping is unreadable") from exc
    if type(b) is not int or b != 90:
        raise ValueError("emulator's effective DS B mapping is not Qt::Key_Z")
    return "isolated-home"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--expected-home", type=Path, required=True)
    args = parser.parse_args()
    try:
        origin = inspect(args.pid, args.expected_home)
    except (ValueError, OSError) as exc:
        parser.exit(1, "FAIL: melonDS input config: " + str(exc) + "\n")
    print("PASS: running melonDS uses verified " + origin + " DS B mapping")


if __name__ == "__main__":
    main()
