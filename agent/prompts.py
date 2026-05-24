from __future__ import annotations

from typing import Optional

from core.runners.base import ExecutionResult

SYSTEM_PROMPT: str = (
    "You are an autonomous code debugger. Given a source file and execution "
    "failure details, produce the complete corrected source in exactly one "
    "markdown fenced code block tagged python or cpp. Output only that block."
)


def generate_user_prompt(
    source_code: str,
    result: ExecutionResult,
    past_fix: Optional[dict[str, str]] = None,
) -> str:
    sections: list[str] = [
        "Source file:",
        source_code,
        "",
        f"Stage: {result.stage}",
        f"Exit code: {result.exit_code}",
        f"Runtime (ms): {result.runtime_ms}",
    ]
    if result.stdout:
        sections.extend(["", "stdout:", result.stdout])
    if result.stderr:
        sections.extend(["", "stderr:", result.stderr])
    if result.error:
        sections.extend(["", f"Error: {result.error}"])
    if result.line_number is not None:
        sections.extend(["", f"Line: {result.line_number}"])
    if past_fix:
        sections.extend(
            [
                "",
                "Similar past failure:",
                past_fix.get("error_trace", ""),
                "",
                "Successful patch from memory:",
                past_fix.get("successful_patch", ""),
            ]
        )
    sections.extend(
        [
            "",
            "Return the full fixed file in a single ```python or ```cpp code block.",
        ]
    )
    return "\n".join(sections)
