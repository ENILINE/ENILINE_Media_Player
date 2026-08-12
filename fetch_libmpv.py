"""Download libmpv-2.dll from the latest shinchiro/mpv-winbuild-cmake release into bin/."""
import json
import os
import shutil
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, "bin")
REPO = "shinchiro/mpv-winbuild-cmake"


def api(url):
    req = urllib.request.Request(url, headers={"User-Agent": "fetch_libmpv"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def find_asset():
    latest = api(f"https://api.github.com/repos/{REPO}/releases/latest")
    assets = latest.get("assets", [])
    # Prefer non-v3 x86_64 build for compatibility.
    for name in ("mpv-dev-x86_64-", "mpv-dev-x86_64-v3-"):
        for a in assets:
            if a["name"].startswith(name) and a["name"].endswith(".7z"):
                return a
    raise SystemExit("No matching mpv-dev-x86_64 .7z asset found.")


def extract(dll_data, dest_dir):
    exe = shutil.which("7z") or shutil.which("7za") or shutil.which("7zr")
    if not exe:
        for p in (r"C:\Program Files\7-Zip\7z.exe", r"C:\Program Files (x86)\7-Zip\7z.exe"):
            if os.path.exists(p):
                exe = p
                break
    if not exe:
        raise SystemExit("7-Zip not found; install it or put 7z.exe on PATH.")
    archive = os.path.join(BIN, "_tmp.7z")
    with open(archive, "wb") as f:
        f.write(dll_data)
    try:
        result = subprocess.run(
            [exe, "x", archive, f"-o{dest_dir}", "-y", "libmpv-2.dll"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise SystemExit(f"7z failed:\n{result.stdout}\n{result.stderr}")
    finally:
        os.remove(archive)
    found = os.path.join(dest_dir, "libmpv-2.dll")
    if not os.path.exists(found):
        raise SystemExit("libmpv-2.dll not found inside archive.")
    return found


def main():
    os.makedirs(BIN, exist_ok=True)
    asset = find_asset()
    print(f"Downloading {asset['name']} ...")
    req = urllib.request.Request(
        asset["browser_download_url"], headers={"User-Agent": "fetch_libmpv"}
    )
    with urllib.request.urlopen(req) as r:
        data = r.read()
    print(f"Downloaded {len(data) / 1e6:.1f} MB, extracting libmpv-2.dll ...")
    tmp = os.path.join(BIN, "_extract")
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp, exist_ok=True)
    src = extract(data, tmp)
    dest = os.path.join(BIN, "libmpv-2.dll")
    shutil.move(src, dest)
    shutil.rmtree(tmp)
    print(f"OK: {dest}")


if __name__ == "__main__":
    sys.exit(main())