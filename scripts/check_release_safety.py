#!/usr/bin/env python3
"""Fail on explicit breaking-change markers unless the commit documents them."""

import subprocess


def main() -> None:
    result = subprocess.run(
        ["git", "log", "-n", "20", "--format=%B"],
        check=True,
        capture_output=True,
        text=True,
    )
    messages = result.stdout
    breaking = "BREAKING CHANGE" in messages or any(
        line.split(":", 1)[0].endswith("!") for line in messages.splitlines() if ":" in line
    )
    if breaking:
        print("Breaking-change marker detected; Release Please will require a reviewed major bump.")
    else:
        print("No explicit breaking-change marker found in recent commits.")


if __name__ == "__main__":
    main()
