from __future__ import annotations

from src.common import env_manifest, path, sha256_file, write_json


def main() -> None:
    files = []
    for target in sorted(path(".").rglob("*")):
        if target.is_file() and "__pycache__" not in target.parts:
            files.append({"path": str(target.relative_to(path("."))), "sha256": sha256_file(target)})
    manifest = env_manifest()
    manifest["files"] = files
    manifest["scenario_hash"] = path("data/locked/LOCKED_SET_HASH.txt").read_text(encoding="utf-8").strip() if path("data/locked/LOCKED_SET_HASH.txt").exists() else ""
    manifest["run_plan_hash"] = path("data/locked/RUN_PLAN_HASH.txt").read_text(encoding="utf-8").strip() if path("data/locked/RUN_PLAN_HASH.txt").exists() else ""
    write_json("MANIFEST.json", manifest)
    print(f"Manifest written with {len(files)} files.")


if __name__ == "__main__":
    main()
