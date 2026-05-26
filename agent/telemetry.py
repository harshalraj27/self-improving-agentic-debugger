import json
import time
from pathlib import Path
import difflib
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional

@dataclass
class StateEvent:
    state: str
    cycle_index: int
    timestamp_offset_ms: int
    duration_ms: int
    metadata: dict

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class TelemetryTracer:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.start_wall_time: float = time.perf_counter()
        self.trajectory: List[StateEvent] = []
        self.active_state: Optional[dict] = None

    def start_state_capture(self, state_name: str, cycle_index: int) -> None:
        current_time = time.perf_counter()
        offset_ms = (current_time - self.start_wall_time) * 1000.0

        self.active_state = {
            "start_time_raw": current_time,
            "state_name": state_name,
            "cycle_index": cycle_index,
            "offset_ms": offset_ms,
            "metadata": {}
        }

    def stop_state_capture(self, metadata: dict) -> None:
        if self.active_state is None:
            raise RuntimeError("A state stop hook was fired without a corresponding start hook.")

        current_time = time.perf_counter()
        duration_ms = (current_time - self.active_state["start_time_raw"]) * 1000.0

        event_obj = StateEvent(
            state=self.active_state["state_name"],
            cycle_index=self.active_state["cycle_index"],
            timestamp_offset_ms=self.active_state["offset_ms"],
            duration_ms=duration_ms,
            metadata=metadata
        )

        self.trajectory.append(event_obj.to_dict())

        self.active_state = None

    @staticmethod
    def _estimate_tokens(payload: str) -> float:
        return len(payload) / 4.0

    def _calculate_metrics_and_deltas(self, initial_code: str, final_code: str) -> tuple:
        total_tokens = 0.0
        for event in self.trajectory:
            if event.get("state") == "ACTION_SELECTED":
                meta = event.get("metadata", {})
                prompt_payload = meta.get("prompt", "")
                output_payload = meta.get("output", "")

                total_tokens += self._estimate_tokens(prompt_payload)
                total_tokens += self._estimate_tokens(output_payload)

        matcher = difflib.SequenceMatcher(None, initial_code, final_code)
        ratio = matcher.ratio()

        delta_code_similarity = 1.0 - ratio

        return total_tokens, delta_code_similarity

    def _build_payload(self, success: bool, total_tokens: float, delta_code_similarity: float) -> dict:
        if total_tokens == 0.0:
            efficiency_score = 0.0
        else:
            efficiency_score = (delta_code_similarity / total_tokens) * 1000

        total_execution_time_ms = (time.perf_counter() - self.start_wall_time) * 1000.0

        if self.trajectory:
            total_retry_cycles = max(event["cycle_index"] for event in self.trajectory)
        else:
            total_retry_cycles = 0

        payload = {
            "job_id": self.job_id,
            "overall_metrics": {
                "total_execution_time_ms": total_execution_time_ms,
                "total_retry_cycles": total_retry_cycles,
                "success": success,
                "efficiency_score": efficiency_score
            },
            "trajectory": self.trajectory
        }
        return payload

    def finalize_trace(self, success: bool, initial_code: str, final_code: str) -> Path:
        total_tokens, delta_code_similarity = self._calculate_metrics_and_deltas(initial_code, final_code)

        document_payload = self._build_payload(success, total_tokens, delta_code_similarity)

        base_dir = Path("data/telemetry")
        base_dir.mkdir(parents=True, exist_ok=True)

        file_path = base_dir / f"trace_{self.job_id}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(document_payload, f, indent=2)

        return file_path