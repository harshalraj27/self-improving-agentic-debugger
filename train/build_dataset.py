from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from agent.prompts import SYSTEM_PROMPT


def compile_trajectory_dataset(telemetry_dir: str = "data/telemetry",
                               output_path: str = "data/tuning_dataset.jsonl") -> None:
    source_path = Path(telemetry_dir)
    target_file = Path(output_path)

    if not source_path.exists():
        print(f"[!] Target telemetry directory '{telemetry_dir}' does not exist.")
        return

    target_file.parent.mkdir(parents=True, exist_ok=True)
    dataset_records: List[Dict[str, Any]] = []

    print(f"[*] Parsing trace records inside {source_path.resolve()}...")

    for trace_path in source_path.glob("*.json"):
        try:
            with open(trace_path, "r", encoding="utf-8") as f:
                trace_data = json.load(f)
        except (json.JSONDecodeError, IOError) as exc:
            print(f"[Warning] Failed to read {trace_path.name}: {exc}")
            continue

        metrics = trace_data.get("overall_metrics", {})
        if not metrics.get("success", False):
            continue

        trajectory = trace_data.get("trajectory", [])

        for step in trajectory:
            if step.get("state") != "ACTION_SELECTED":
                continue

            metadata = step.get("metadata", {})
            user_prompt = metadata.get("prompt")
            model_output = metadata.get("output")

            if not user_prompt or not model_output:
                continue

            record = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": model_output}
                ]
            }
            dataset_records.append(record)

    if not dataset_records:
        print("[!] No successful evaluation trajectory records matched fine-tuning criteria.")
        return

    with open(target_file, "w", encoding="utf-8") as out_f:
        for record in dataset_records:
            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"[+] Successfully compiled {len(dataset_records)} high-efficiency training shards into: {target_file}")


if __name__ == "__main__":
    compile_trajectory_dataset()