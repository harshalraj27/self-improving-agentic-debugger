from __future__ import annotations

import os
from pathlib import Path

TARGET_DIR = Path("data") / "benchmarks"

BENCHMARK_FILES: dict[str, str] = {
    "py_syntax.py": """if True
    print("syntax check failed")
""",
    "py_runtime_logic.py": """def run_calculations() -> None:
    for i in range(5):
        value = 100 / (i - 2)
        print(value)


if __name__ == "__main__":
    run_calculations()
""",
    "py_type_error.py": """def build_label(count: int) -> str:
    return "items: " + count


if __name__ == "__main__":
    print(build_label(3))
""",
    "cpp_syntax.cpp": """#include <iostream>

int main() {
    std::cout << "syntax benchmark" << std::endl;
    return 0;
""",
    "cpp_runtime.cpp": """#include <iostream>

int main() {
    int* ptr = nullptr;
    std::cout << *ptr << std::endl;
    return 0;
}
""",
    "cpp_type_mismatch.cpp": """int get_score() {
    return "invalid";
}

int main() {
    return get_score();
}
""",
}


def main() -> None:
    os.makedirs(TARGET_DIR, exist_ok=True)

    for filename, source in BENCHMARK_FILES.items():
        file_path = TARGET_DIR / filename
        file_path.write_text(source, encoding="utf-8")
        print(f"[benchmarks] wrote {file_path.as_posix()}")


if __name__ == "__main__":
    main()
