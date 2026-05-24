from __future__ import annotations

from core.runners.base import ExecutionResult

SYSTEM_PROMPT: str = (
    "You are an autonomous code debugger. Given a source file and execution "
    "failure details, produce the complete corrected source in exactly one "
    "markdown fenced code block tagged python or cpp. Output only that block."
)


def generate_user_prompt(source_code: str, result: ExecutionResult) -> str:
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
    sections.extend(
        [
            "",
            "Return the full fixed file in a single ```python or ```cpp code block.",
        ]
    )
    return "\n".join(sections)
