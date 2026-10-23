"""Resolve bot-compatible custom builds and filter upstream build matrices.

Standard library only. Reads workflow inputs from environment variables and
writes single-line outputs to GITHUB_OUTPUT; never starts a build or uses GitHub.
"""

import argparse
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANDROID = {
    "5.10": "android12",
    "5.15": "android13",
    "6.1": "android14",
    "6.6": "android15",
    "6.12": "android16",
}


def load_versions(kernel, root=ROOT):
    if kernel not in ANDROID:
        raise ValueError(f"Unsupported kernel version: {kernel}")
    path = root / "data" / ANDROID[kernel] / f"{kernel}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise TypeError(f"Invalid version catalog: {path}")
    return data


def resolve_custom(kernel, patch, expected="", revision="r1", root=ROOT):
    data = load_versions(kernel, root)
    patch, expected = patch.strip(), expected.strip().upper()
    if patch.lower() == "lts":
        if kernel == "6.12":
            raise ValueError(
                "6.12 LTS is disabled upstream; choose a dated Android 16 release"
            )
        full, sub = data.get("lts", ""), "X"
        patch = "lts"
    else:
        entry = next(
            (entry for entry in data["entries"] if entry.get("date") == patch), None
        )
        if not entry:
            raise ValueError(f"No {kernel} release matches patch level {patch}")
        full = entry.get("kernel", "")
        sub = full.rsplit(".", 1)[-1]
    if not re.fullmatch(re.escape(kernel) + r"\.\d+", full):
        raise ValueError(f"Invalid kernel version in catalog: {full}")
    if expected and expected != sub:
        raise ValueError(
            f"Requested {kernel}.{expected}, but {patch} resolves to {full}; refusing a different build"
        )
    revision = revision.strip() or "r1"
    if not re.fullmatch(r"r\d+", revision):
        raise ValueError("revision must be r followed by digits")
    return {
        "android_version": ANDROID[kernel],
        "kernel_full": full,
        "sub_level": sub,
        "os_patch_level": patch,
        "revision": revision,
    }


def filter_matrix(matrix, requested, kernel, root=ROOT):
    """Keep upstream defaults, but allow a bot to select newer catalog entries."""
    if (
        not isinstance(matrix, list)
        or not matrix
        or any(not isinstance(row, dict) for row in matrix)
    ):
        raise ValueError("The upstream matrix must be a non-empty list of objects")
    if not requested.strip():
        return {"include": matrix}
    tokens = list(
        dict.fromkeys(token.strip().upper() for token in requested.split(","))
    )
    if len(tokens) > 256:
        raise ValueError("A workflow matrix cannot exceed 256 builds")
    if any(not re.fullmatch(r"(?:\d+|X)", token) for token in tokens):
        raise ValueError("sub_levels must be comma-separated numbers or X")
    selected = []
    data = load_versions(kernel, root)
    for token in tokens:
        if token == "X" and kernel == "6.12":
            raise ValueError("6.12 LTS is disabled upstream; choose a dated release")
        row = next(
            (dict(row) for row in matrix if str(row.get("sub_level")).upper() == token),
            None,
        )
        if row is None:
            matches = [
                entry
                for entry in data["entries"]
                if entry.get("kernel") == f"{kernel}.{token}"
            ]
            if token == "X" and data.get("lts"):
                row = {"sub_level": "X", "os_patch_level": "lts", "revision": "r1"}
            elif matches:
                # A sublevel may have multiple patch dates; choose the newest.
                entry = max(matches, key=lambda entry: entry["date"])
                row = {
                    "sub_level": token,
                    "os_patch_level": entry["date"],
                    "revision": "r1",
                }
            else:
                raise ValueError(
                    f"Unknown sublevel {token} for {kernel}; no builds dispatched"
                )
        selected.append(row)
    return {"include": selected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("custom", "matrix"))
    args = parser.parse_args()
    try:
        kernel = os.environ["KERNEL_VERSION"]
        if args.command == "custom":
            values = resolve_custom(
                kernel,
                os.environ["OS_PATCH_LEVEL"],
                os.getenv("SUB_LEVEL", ""),
                os.getenv("REVISION", "r1"),
            )
            android = os.getenv("ANDROID_VERSION", "").strip()
            if android and android != values["android_version"]:
                raise ValueError("Android and kernel versions do not match")
        else:
            if os.getenv("ANDROID_VERSION") != ANDROID.get(kernel):
                raise ValueError("Android and kernel versions do not match")
            matrix = filter_matrix(
                json.loads(os.environ["MATRIX_JSON"]),
                os.getenv("SUB_LEVELS", ""),
                kernel,
            )
            values = {
                "matrix": json.dumps(matrix, ensure_ascii=False, separators=(",", ":"))
            }
        with open(
            os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8", newline="\n"
        ) as stream:
            stream.writelines(f"{key}={value}\n" for key, value in values.items())
        print(json.dumps(values, ensure_ascii=True))
    except (KeyError, OSError, TypeError, ValueError) as error:
        parser.exit(1, f"Workflow input error: {error}\n")


if __name__ == "__main__":
    main()
