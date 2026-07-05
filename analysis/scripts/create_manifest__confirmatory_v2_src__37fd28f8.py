from __future__ import annotations

from src.common import environment_manifest, path, sha256_file, write_json


def main() -> None:
    files = []
    for rel_root in ["config", "schemas", "src", "data/internal", "data/model_visible", "prompts", "results", "reports"]:
        for target in sorted(path(rel_root).rglob("*")):
            if target.is_file():
                files.append({"path": str(target.relative_to(path("."))), "sha256": sha256_file(target)})
    manifest = environment_manifest()
    manifest["files"] = files
    manifest["no_api_calls_sent_by_pipeline"] = True
    write_json("logs/manifest.json", manifest)
    print(f"Manifest files: {len(files)}")


if __name__ == "__main__":
    main()
