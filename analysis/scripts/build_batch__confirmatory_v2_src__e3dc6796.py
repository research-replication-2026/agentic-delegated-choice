from __future__ import annotations

import json

from src.common import path, read_json


def main() -> None:
    prompts = read_json("prompts/confirmatory_prompts.json")["prompts"]
    target = path("data/internal/future_api_batch_preview.jsonl")
    with target.open("w", encoding="utf-8") as f:
        for idx, p in enumerate(prompts):
            f.write(json.dumps({
                "custom_id": f"{p['scenario_id']}__{p['condition']}__template",
                "method": "POST",
                "url": "/v1/responses",
                "body_preview_only": True,
                "tool_name": "submit_agentic_decision",
                "messages": [
                    {"role": "system", "content": p["system_instruction"]},
                    {"role": "user", "content": json.dumps(p["user_payload"], ensure_ascii=False)},
                ],
            }, ensure_ascii=False) + "\n")
    print(f"Built non-submitted batch preview: {target}")


if __name__ == "__main__":
    main()
