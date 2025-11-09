#!/usr/bin/env python3
print("🟢 Starting Supabase upload script…")

import os
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv
import argparse

# ─── Load Environment ─────────────────────────────────────────────
load_dotenv()

if "SUPABASE_URL" not in os.environ or "SUPABASE_SERVICE_ROLE_KEY" not in os.environ:
    raise RuntimeError("❌ Supabase credentials not found in environment variables.")

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
supabase = create_client(url, key)

# ─── Parse Arguments ─────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Upload datasets to Supabase storage.")
parser.add_argument('--overwrite', action='store_true', help='Overwrite existing files in Supabase storage')
args = parser.parse_args()

overwrite = args.overwrite
print(f"Overwrite mode: {overwrite}")

# ─── Directories ──────────────────────────────────────────────────
base_dir = Path(__file__).resolve().parent.parent.parent.parent
processed_dir = base_dir / "data" / "processed"
telegram_dir = processed_dir / "telegram"
final_chunks_dir = base_dir / "data" / "chunks" / "final"

# ─── Helper: Find latest + symlink ────────────────────────────────
def find_and_link_latest(prefix: str, directory: Path) -> tuple:
    files = sorted(directory.glob(f"{prefix}*.json"))
    if not files:
        print(f"⚠️ No file found for {prefix} in {directory}")
        return None, None

    latest = files[-1]
    symlink = directory / f"{prefix}_latest.json"

    if symlink.exists() or symlink.is_symlink():
        symlink.unlink()
    symlink.symlink_to(latest.name)

    print(f"🔗 {symlink.name} → {latest.name}")
    return latest, symlink

# ─── Helper: Upload file to Supabase ──────────────────────────────
def upload(remote_path: str, local_file: Path) -> None:
    try:
        if overwrite:
            # Try to delete the file first (ignore errors if it doesn't exist)
            try:
                supabase.storage.from_("datasets").remove([remote_path])
                print(f"🗑️ Deleted existing file {remote_path} before upload (overwrite mode)")
            except Exception as del_e:
                print(f"⚠️ Could not delete {remote_path} before upload: {del_e}")
        with open(local_file, "rb") as f:
            supabase.storage.from_("datasets").upload(
                path=remote_path,
                file=f,
                file_options={"content-type": "application/json"}
            )
        print(f"✅ Uploaded {local_file.name} → {remote_path}")
    except Exception as e:
        print(f"❌ Upload failed for {local_file.name} → {remote_path}")
        print(e)

# ─── Upload Targets ───────────────────────────────────────────────
upload_targets = [
    ("all_pyq_base", processed_dir),
    ("all_pyq_mvp", telegram_dir),
    ("all_pyq_enriched", processed_dir),
    ("final_chunks_20250725_1818", final_chunks_dir),
]

for prefix, directory in upload_targets:
    latest, symlink = find_and_link_latest(prefix, directory)
    if latest:
        # Upload dated version
        upload(f"{directory.name}/{latest.name}", latest)
    if symlink:
        # Upload _latest symlink version
        upload(f"{directory.name}/{symlink.name}", symlink)

print("🚀 Upload script complete.")
