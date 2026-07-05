from __future__ import annotations

import json
import os

from src.common import load_yaml, path, write_json
from src.build_batch import metadata_validation_errors


def main() -> None:
    cfg = load_yaml("config/experiment.yaml")
    batch = path(os.environ.get("BATCH_FILE", cfg["batch_file"]))
    issues = []
    count = 0
    custom_ids = set()
    with batch.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            count += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                issues.append(f"line {line_no}: {exc}")
                continue
            custom_ids.add(rec.get("custom_id"))
            if rec.get("method") != "POST":
                issues.append(f"line {line_no}: method is not POST")
            if rec.get("url") != "/v1/responses":
                issues.append(f"line {line_no}: unexpected url")
            body = rec.get("body", {})
            metadata = body.get("metadata", {})
            if metadata.get("simulation_only") != "true":
                issues.append(f"line {line_no}: simulation_only metadata must be string 'true'")
            for issue in metadata_validation_errors(metadata):
                issues.append(f"line {line_no}: {issue}")
            tools = body.get("tools") or []
            if not tools or tools[0].get("name") != "submit_agentic_decision":
                issues.append(f"line {line_no}: wrong tool")
    if count != 2000:
        issues.append(f"Expected 2000 requests, got {count}")
    if len(custom_ids) != count:
        issues.append("custom_id values are not unique")
    write_json("logs/batch_validation.json", {"valid": not issues, "requests": count, "issues": issues})
    if issues:
        raise SystemExit("; ".join(issues[:10]))
    print("Batch validation passed.")


if __name__ == "__main__":
    main()
