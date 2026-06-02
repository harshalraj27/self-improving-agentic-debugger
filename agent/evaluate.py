import json
import os
import shutil
import time
from difflib import SequenceMatcher
from pathlib import Path
import matplotlib.pyplot as plt

class DummyAgent:
    def __init__(self, target_file_path: Path):
        self.target_file_path = target_file_path
        self.job_id = f"eval_{int(time.time() * 1000)}_{target_file_path.stem}"

    def run(self):
        is_cpp = self.target_file_path.suffix == ".cpp"
        success = True if "syntax" in self.target_file_path.name else False
        retries = 3 if is_cpp else 1
        latency = 4500.5 if is_cpp else 1250.2
        efficiency = 85.5 if success else 0.0
        rag_hit_value = True if not is_cpp else False

        trajectory = [
            {
                "state": "READY",
                "cycle_index": 0,
                "timestamp_offset_ms": 10.5,
                "duration_ms": 150.0,
                "metadata": {"sandbox_stage": "Initialization"}
            },
            {
                "state": "ACTION_SELECTED",
                "cycle_index": 0,
                "timestamp_offset_ms": 160.5,
                "duration_ms": 800.0,
                "metadata": {
                    "estimated_prompt_tokens": 350,
                    "estimated_output_tokens": 120,
                    "rag_memory_hit": rag_hit_value
                }
            }
        ]

        payload = {
            "job_id": self.job_id,
            "overall_metrics": {
                "total_execution_time_ms": latency,
                "total_retry_cycles": retries,
                "system_convergence_success": success,
                "token_expenditure_efficiency": efficiency
            },
            "trajectory": trajectory
        }

        telemetry_dir = Path("data/telemetry")
        telemetry_dir.mkdir(parents=True, exist_ok=True)
        trace_path = telemetry_dir / f"trace_{self.job_id}.json"
        with open(trace_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

def setup_mock_benchmarks():
    bench_dir = Path("data/benchmarks")
    bench_dir.mkdir(parents=True, exist_ok=True)

    (bench_dir / "broken_syntax.py").write_text("def broken_function()\n    print('Missing Colon')", encoding="utf-8")
    (bench_dir / "logical_leak.py").write_text("while True:\n    pass # Infinite Loop Error", encoding="utf-8")
    (bench_dir / "compile_error.cpp").write_text("int main() { std::cout << 'Missing header' }", encoding="utf-8")



def run_evaluation_suite():
    benchmark_dir = Path("data/benchmarks")
    scratch_dir = Path("data/evaluation_scratch")
    telemetry_dir = Path("data/telemetry")

    if scratch_dir.exists():
        shutil.rmtree(scratch_dir)
    scratch_dir.mkdir(parents=True, exist_ok=True)

    benchmark_files = []
    for ext in ("*.py", "*.cpp"):
        benchmark_files.extend(benchmark_dir.glob(ext))

    if not benchmark_files:
        print("[!] No benchmark assets detected. Running initial mock setup helper...")
        setup_mock_benchmarks()
        for ext in ("*.py", "*.cpp"):
            benchmark_files.extend(benchmark_dir.glob(ext))

    evaluation_records = []

    print(f"[*] Core initialized. Processing {len(benchmark_files)} benchmark assets across isolation layer...")

    for asset_path in benchmark_files:
        timestamp_token = int(time.time() * 1000)
        scratch_filename = f"eval_{timestamp_token}_{asset_path.name}"
        scratch_file_target = scratch_dir / scratch_filename

        shutil.copy2(asset_path, scratch_file_target)

        agent_instance = DummyAgent(scratch_file_target)
        agent_instance.run()

        associated_job_id = agent_instance.job_id

        trace_file_path = telemetry_dir / f"trace_{associated_job_id}.json"

        if not trace_file_path.exists():
            print(f"[Warning] Telemetry trace file missing for Job ID: {associated_job_id}. Skipping record.")
            continue

        with open(trace_file_path, "r", encoding="utf-8") as f:
            trace_data = json.load(f)

        overall_metrics = trace_data.get("overall_metrics", {})
        trajectory = trace_data.get("trajectory", [])

        success_outcome = overall_metrics.get("system_convergence_success", False)
        total_latency = overall_metrics.get("total_execution_time_ms", 0.0)
        retry_cycles = overall_metrics.get("total_retry_cycles", 0)
        efficiency_score = overall_metrics.get("token_expenditure_efficiency", 0.0)

        rag_hits_count = 0
        for step in trajectory:
            metadata = step.get("metadata", {})
            if metadata.get("rag_memory_hit") is True:
                rag_hits_count += 1

        evaluation_records.append({
            "filename": asset_path.name,
            "language": asset_path.suffix.replace(".", ""),
            "success": success_outcome,
            "latency_ms": total_latency,
            "retry_cycles": retry_cycles,
            "efficiency_score": efficiency_score,
            "rag_hits": rag_hits_count
        })

    if not evaluation_records:
        print("[!] Execution loop finished with zero telemetry outputs recorded. Terminating.")
        return

    total_jobs = len(evaluation_records)
    successful_jobs = sum(1 for rec in evaluation_records if rec["success"])
    system_convergence_rate = (successful_jobs / total_jobs) * 100.0

    python_latencies = [rec["latency_ms"] for rec in evaluation_records if rec["language"] == "py"]
    cpp_latencies = [rec["latency_ms"] for rec in evaluation_records if rec["language"] == "cpp"]

    avg_py_latency = sum(python_latencies) / len(python_latencies) if python_latencies else 0.0
    avg_cpp_latency = sum(cpp_latencies) / len(cpp_latencies) if cpp_latencies else 0.0

    rag_active_group = [rec for rec in evaluation_records if rec["rag_hits"] > 0]
    rag_cold_group = [rec for rec in evaluation_records if rec["rag_hits"] == 0]

    avg_rag_retries = sum(r["retry_cycles"] for r in rag_active_group) / len(
        rag_active_group) if rag_active_group else 0.0
    avg_cold_retries = sum(r["retry_cycles"] for r in rag_cold_group) / len(rag_cold_group) if rag_cold_group else 0.0

    avg_rag_efficiency = sum(r["efficiency_score"] for r in rag_active_group) / len(
        rag_active_group) if rag_active_group else 0.0
    avg_cold_efficiency = sum(r["efficiency_score"] for r in rag_cold_group) / len(
        rag_cold_group) if rag_cold_group else 0.0

    report_path = Path("evaluation_report.md")
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write("# System Performance Audit Report\n\n")
        rf.write("## High-Level System Performance Matrices\n")
        rf.write(f"* **Overall System Convergence Rate:** {system_convergence_rate:.2f}%\n")
        rf.write(f"* **Average Python Latency:** {avg_py_latency:.2f} ms\n")
        rf.write(f"* **Average C++ Compilation/Execution Latency:** {avg_cpp_latency:.2f} ms\n\n")

        rf.write("## RAG Cache Impact Summary\n")
        rf.write("| Metric Dimension | Cache Hits (Active) | Cache Misses (Cold) |\n")
        rf.write("| --- | --- | --- |\n")
        rf.write(f"| Average Retry Loop Allocation | {avg_rag_retries:.2f} cycles | {avg_cold_retries:.2f} cycles |\n")
        rf.write(f"| Token Expenditure Efficiency Score | {avg_rag_efficiency:.2f} | {avg_cold_efficiency:.2f} |\n\n")

        rf.write("## Per-File Granular Performance Analytics\n")
        rf.write(
            "| Target Asset Filename | Language | Success Status | Execution Latency | Retries | Efficiency Rank |\n")
        rf.write("| --- | --- | --- | --- | --- | --- |\n")
        for rec in evaluation_records:
            status_symbol = "PASS" if rec["success"] else "FAIL"
            rf.write(
                f"| {rec['filename']} "
                f"| {rec['language'].upper()} "
                f"| {status_symbol} "
                f"| {rec['latency_ms']:.1f} ms "
                f"| {rec['retry_cycles']} "
                f"| {rec['efficiency_score']:.2f} |\n"
            )

    print(f"[+] Automated markdown metric report compiled successfully into: {report_path}")

    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, ax = plt.subplots(figsize=(10, 6))

    py_records = [r for r in evaluation_records if r["language"] == "py"]
    cpp_records = [r for r in evaluation_records if r["language"] == "cpp"]

    ax.scatter(
        [r["retry_cycles"] for r in py_records],
        [r["latency_ms"] for r in py_records],
        color="#3776AB", s=150, alpha=0.85, edgecolors='black', linewidths=1.5, label="Python Target Stack"
    )
    ax.scatter(
        [r["retry_cycles"] for r in cpp_records],
        [r["latency_ms"] for r in cpp_records],
        color="#00599C", s=150, alpha=0.85, edgecolors='black', linewidths=1.5, marker="s",
        label="C++ Compiler Target Stack"
    )

    ax.set_title("System Infrastructure Scaling: Execution Latency Overhead vs. Retry Allocation", fontsize=14,
                 fontweight='bold', pad=15)
    ax.set_xlabel("FSM Retry Loop Allocation Count (Cycles)", fontsize=12, fontweight='semibold')
    ax.set_ylabel("Total Job Processing Latency Footprint (ms)", fontsize=12, fontweight='semibold')

    all_cycles = [r["retry_cycles"] for r in evaluation_records]
    ax.set_xticks(range(min(all_cycles) if all_cycles else 0, (max(all_cycles) if all_cycles else 4) + 2))

    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="none", shadow=True)
    plt.tight_layout()

    chart_path = Path("analytics_chart.png")
    plt.savefig(chart_path, dpi=200)
    plt.close()

    print(f"[+] System analytics visualization asset rendered securely into: {chart_path}")

if __name__ == "__main__":
    run_evaluation_suite()