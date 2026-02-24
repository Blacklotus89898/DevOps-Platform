#!/usr/bin/env python3
"""
Local SRE Agent
- Process monitoring
- Crash detection
- Log aggregation
- Plain-text reports
- Integration with: htop, btop, lazydocker, k9s
"""

import psutil
import time
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# =========================
# CONFIGURATION
# =========================
TARGET_NAME = "python3"
CHECK_INTERVAL = 5
SNAPSHOT_INTERVAL = 60
MEM_THRESHOLD_MB = 200
APP_LOG_PATH = "app.log"
REPORT_DIR = Path("sre_reports")

# Enable interactive helpers on crash (TTY only)
LAUNCH_TUI_ON_CRASH = False


# =========================
# TOOL DETECTION
# =========================
TOOLS = {
    "htop": shutil.which("htop"),
    "btop": shutil.which("btop"),
    "lazydocker": shutil.which("lazydocker"),
    "k9s": shutil.which("k9s"),
}


def tool_status():
    lines = []
    for tool, path in TOOLS.items():
        if path:
            lines.append(f"{tool}: AVAILABLE ({path})")
        else:
            lines.append(f"{tool}: NOT INSTALLED")
    return "\n".join(lines)


# =========================
# UTILITIES
# =========================
def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def find_process(name):
    for p in psutil.process_iter(attrs=["name"]):
        if p.info["name"] and name.lower() in p.info["name"].lower():
            return p
    return None


def tail_file(path, lines=30):
    if not os.path.exists(path):
        return f"Log file not found: {path}"
    try:
        with open(path, "r") as f:
            return "".join(f.readlines()[-lines:])
    except Exception as e:
        return f"Failed to read log: {e}"


def kernel_oom_check():
    try:
        out = subprocess.check_output(
            "dmesg | tail -n 100", shell=True, text=True
        ).lower()
        if "oom" in out:
            return "Possible OOM activity detected in kernel logs."
        return "No OOM events detected."
    except Exception:
        return "Kernel logs unavailable (non-root user)."


def docker_context():
    if not TOOLS["lazydocker"]:
        return "Docker tooling not installed."
    try:
        out = subprocess.check_output(
            "docker ps --format '{{.Names}}'", shell=True, text=True
        )
        return f"Running containers:\n{out.strip()}" if out.strip() else "No running containers."
    except Exception:
        return "Docker not accessible."


def k8s_context():
    if not TOOLS["k9s"]:
        return "Kubernetes tooling not installed."
    try:
        out = subprocess.check_output(
            "kubectl get pods --no-headers 2>/dev/null | head -n 5",
            shell=True,
            text=True,
        )
        return f"Active pods (sample):\n{out.strip()}" if out.strip() else "No pods or no cluster access."
    except Exception:
        return "Kubernetes context unavailable."


# =========================
# REPORT GENERATION
# =========================
def write_report(proc=None, crashed=False):
    REPORT_DIR.mkdir(exist_ok=True)

    ts_file = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_type = "CRASH" if crashed else "SNAPSHOT"
    path = REPORT_DIR / f"{report_type}_{ts_file}.txt"

    if proc and proc.is_running():
        try:
            with proc.oneshot():
                proc_info = (
                    f"PID: {proc.pid}\n"
                    f"Status: {proc.status()}\n"
                    f"CPU Usage: {proc.cpu_percent(interval=0.1)}%\n"
                    f"Memory (RSS): {proc.memory_info().rss / 1024 / 1024:.2f} MB\n"
                    f"Threads: {proc.num_threads()}\n"
                )
        except Exception:
            proc_info = "Process data partially unavailable.\n"
    else:
        proc_info = "PROCESS NOT RUNNING\n"

    report = (
        f"LOCAL SRE REPORT\n"
        f"================\n"
        f"Generated: {now_ts()}\n"
        f"Target Process: {TARGET_NAME}\n"
        f"Report Type: {report_type}\n\n"
        f"PROCESS STATE\n"
        f"-------------\n"
        f"{proc_info}\n"
        f"RESOURCE LIMITS\n"
        f"---------------\n"
        f"Memory Threshold: {MEM_THRESHOLD_MB} MB\n\n"
        f"APPLICATION LOGS (TAIL)\n"
        f"-----------------------\n"
        f"{tail_file(APP_LOG_PATH)}\n\n"
        f"HOST HEALTH\n"
        f"-----------\n"
        f"System RAM Usage: {psutil.virtual_memory().percent}%\n"
        f"Disk Usage (/): {psutil.disk_usage('/').percent}%\n\n"
        f"KERNEL SIGNALS\n"
        f"--------------\n"
        f"{kernel_oom_check()}\n\n"
        f"DOCKER CONTEXT\n"
        f"--------------\n"
        f"{docker_context()}\n\n"
        f"KUBERNETES CONTEXT\n"
        f"------------------\n"
        f"{k8s_context()}\n\n"
        f"AVAILABLE SRE TOOLS\n"
        f"-------------------\n"
        f"{tool_status()}\n\n"
        f"OPERATOR ACTIONS\n"
        f"----------------\n"
        f"- htop / btop : Inspect system load\n"
        f"- lazydocker : Inspect container failures\n"
        f"- k9s        : Inspect pod crashes\n\n"
        f"END OF REPORT\n"
    )

    with open(path, "w") as f:
        f.write(report)

    return path


# =========================
# MAIN LOOP
# =========================
def main():
    print("Local SRE Agent started")
    print(f"Watching process: {TARGET_NAME}")
    print(f"Reports directory: {REPORT_DIR.resolve()}")
    print("Detected tools:")
    print(tool_status())

    last_snapshot = 0

    try:
        while True:
            proc = find_process(TARGET_NAME)
            now = time.time()

            if proc:
                mem_mb = proc.memory_info().rss / 1024 / 1024

                if mem_mb > MEM_THRESHOLD_MB:
                    print(f"WARNING: Memory usage high ({mem_mb:.1f} MB)")

                if now - last_snapshot >= SNAPSHOT_INTERVAL:
                    path = write_report(proc)
                    print(f"Snapshot saved: {path}")
                    last_snapshot = now
            else:
                print(f"CRASH DETECTED: {TARGET_NAME}")
                path = write_report(crashed=True)
                print(f"Crash report saved: {path}")

                if LAUNCH_TUI_ON_CRASH and os.isatty(0):
                    print("Launching htop for investigation...")
                    subprocess.call(["htop"])

                time.sleep(10)

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("SRE Agent stopped.")


if __name__ == "__main__":
    main()