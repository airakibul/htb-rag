"""
fetch_corpus.py – Download and set up the raw HTB writeup corpus.

Clones the raw writeup markdown files from the official repository
(https://github.com/0xh7ml/htb-wiki) into the local `./raw` directory.
"""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_URL = "https://github.com/0xh7ml/htb-wiki.git"
ZIP_URL = "https://github.com/0xh7ml/htb-wiki/archive/refs/heads/main.zip"
TARGET_DIR = Path(__file__).resolve().parent.parent / "raw"


def fetch_via_git(target_dir: Path) -> bool:
    """Attempt shallow git clone of htb-wiki and copy raw/."""
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            print("[*] Shallow-cloning repository from GitHub...")
            cmd = ["git", "clone", "--depth", "1", REPO_URL, tmp_dir]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode != 0:
                return False

            src_raw = Path(tmp_dir) / "raw"
            if not src_raw.exists():
                return False

            print(f"[*] Copying writeup files to {target_dir}...")
            shutil.copytree(src_raw, target_dir, dirs_exist_ok=True)
            return True
    except Exception as exc:
        print(f"[!] Git clone failed: {exc}")
        return False


def fetch_via_zip(target_dir: Path) -> bool:
    """Download repository zip archive and extract raw/."""
    try:
        print(f"[*] Downloading corpus zip archive from {ZIP_URL}...")
        req = urllib.request.Request(ZIP_URL, headers={"User-Agent": "HTB-RAG-Corpus-Fetcher"})
        with urllib.request.urlopen(req) as resp:
            data = resp.read()

        print("[*] Extracting raw writeup files...")
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            target_dir.mkdir(parents=True, exist_ok=True)
            copied = 0
            for member in zf.namelist():
                # Members match 'htb-wiki-main/raw/...'
                if "/raw/" in member and not member.endswith("/"):
                    filename = Path(member).name
                    dest_file = target_dir / filename
                    with zf.open(member) as src, open(dest_file, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    copied += 1
            print(f"[+] Extracted {copied} files.")
            return copied > 0
    except Exception as exc:
        print(f"[-] Zip download failed: {exc}")
        return False


def main() -> None:
    if TARGET_DIR.exists() and any(TARGET_DIR.glob("*.md")):
        count = len(list(TARGET_DIR.glob("*.md")))
        print(f"[+] Corpus already present at {TARGET_DIR} ({count} markdown files).")
        return

    print("[*] Fetching HTB writeup corpus...")
    success = fetch_via_git(TARGET_DIR)
    if not success:
        print("[*] Falling back to direct zip download...")
        success = fetch_via_zip(TARGET_DIR)

    if success:
        count = len(list(TARGET_DIR.glob("*.md")))
        print(f"[+] Success! {count} writeup files ready in {TARGET_DIR}.")
    else:
        print("[-] Failed to fetch dataset automatically.")
        print(f"Please manually clone https://github.com/0xh7ml/htb-wiki and place the 'raw' folder into {TARGET_DIR}.")
        sys.exit(1)


if __name__ == "__main__":
    main()
