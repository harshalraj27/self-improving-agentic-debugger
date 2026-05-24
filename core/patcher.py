from __future__ import annotations

import re
from pathlib import Path

_CODE_BLOCK_PATTERN = re.compile(
    r"```(?:python|cpp)\s*\r?\n(.*?)\r?\n\s*```",
    re.DOTALL,
)


def apply_patch(file_path: str, raw_llm_output: str) -> bool:
    matches = _CODE_BLOCK_PATTERN.findall(raw_llm_output)
    if len(matches) != 1:
        return False

    content = matches[0].strip("\r\n")
    Path(file_path).write_text(content, encoding="utf-8", newline="\n")
    return True
