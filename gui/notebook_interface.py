# -*- coding: utf-8 -*-
"""
notebook_interface.py — Jupyter Notebook interface for Process Monitor.

Provides high-level, notebook-friendly functions to fetch, display,
filter, and control OS processes via the C++ backend.  This module has
**zero** Tkinter dependencies and is designed to be used exclusively
inside Jupyter / IPython environments.

Usage (inside a notebook cell):

    from gui.notebook_interface import *

    display_processes()          # one-shot table
    live_monitor(interval=3)    # auto-refreshing table
    kill_process(1234)          # process control
    plot_cpu_usage()            # CPU trend chart
"""

from __future__ import annotations

import csv
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Ensure the parent directory of `gui/` is on sys.path so that the
# backend_bridge module can locate the backend binary relative to itself,
# regardless of the working directory the notebook was launched from.
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)

if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

# ---------------------------------------------------------------------------
# Lazy / guarded imports for notebook-only dependencies
# ---------------------------------------------------------------------------
import pandas as pd  # noqa: E402

try:
    from IPython.display import display, clear_output, HTML
    _HAS_IPYTHON = True
except ImportError:
    _HAS_IPYTHON = False

try:
    import matplotlib.pyplot as plt
    _HAS_MATPLOTLIB = True
except ImportError:
    _HAS_MATPLOTLIB = False

# Import the backend bridge (our own module — no Tkinter involved)
from backend_bridge import BackendBridge  # noqa: E402


# ---------------------------------------------------------------------------
# Safe print helper — emojis work in Jupyter (UTF-8) but can crash on
# Windows consoles that use cp1252.  This wrapper degrades gracefully.
# ---------------------------------------------------------------------------
def _safe_print(*args: Any, **kwargs: Any) -> None:
    """Print with automatic fallback for non-UTF-8 terminals."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        text = " ".join(str(a) for a in args)
        print(text.encode("ascii", errors="replace").decode("ascii"), **kwargs)

# ---------------------------------------------------------------------------
# Module-level singleton bridge instance (lazy)
# ---------------------------------------------------------------------------
_bridge: Optional[BackendBridge] = None


def _get_bridge() -> BackendBridge:
    """Return (and lazily create) a shared BackendBridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = BackendBridge()
    return _bridge


# ---------------------------------------------------------------------------
# Public API — exported via wildcard import
# ---------------------------------------------------------------------------
__all__ = [
    "fetch_processes",
    "processes_to_dataframe",
    "filter_processes",
    "sort_processes",
    "display_processes",
    "live_monitor",
    "kill_process",
    "pause_process",
    "resume_process",
    "set_priority",
    "plot_cpu_usage",
    "search_process",
    "export_to_csv",
]


# ── 1. Fetch Data ────────────────────────────────────────────────────
def fetch_processes() -> List[Dict[str, Any]]:
    """Fetch the current process list from the C++ backend.

    Returns:
        A list of dicts, each containing keys:
        ``pid``, ``name``, ``state``, ``cpu``, ``memory``.
        Returns an empty list on any backend error.
    """
    try:
        return _get_bridge().list_processes()
    except Exception:
        return []


# ── 2. Convert to DataFrame ──────────────────────────────────────────
def processes_to_dataframe(
    processes: List[Dict[str, Any]],
) -> pd.DataFrame:
    """Convert a list of process dicts into a pandas DataFrame.

    Columns: PID, Name, Status, CPU, Memory
    """
    if not processes:
        return pd.DataFrame(columns=["PID", "Name", "Status", "CPU", "Memory"])

    rows = []
    for p in processes:
        rows.append(
            {
                "PID": int(p.get("pid", 0)),
                "Name": str(p.get("name", "")),
                "Status": str(p.get("state", "")),
                "CPU": float(p.get("cpu", 0.0)),
                "Memory": float(p.get("memory", 0.0)),
            }
        )
    return pd.DataFrame(rows)


# ── 3. Filter Data ───────────────────────────────────────────────────
def filter_processes(df: pd.DataFrame) -> pd.DataFrame:
    """Remove low-usage and system processes.

    Filters out:
      - Rows where CPU < 0.1 **and** Memory < 5
      - Rows where PID <= 4 (system/idle processes)
    """
    if df.empty:
        return df

    # Remove system PIDs
    df = df[df["PID"] > 4]

    # Remove low-usage processes (both conditions must be true)
    low_usage = (df["CPU"] < 0.1) & (df["Memory"] < 5)
    df = df[~low_usage]

    return df.reset_index(drop=True)


# ── 4. Sort Data ─────────────────────────────────────────────────────
def sort_processes(df: pd.DataFrame) -> pd.DataFrame:
    """Sort processes by CPU usage in descending order."""
    if df.empty:
        return df
    return df.sort_values("CPU", ascending=False).reset_index(drop=True)


# ── 5. Display Table ─────────────────────────────────────────────────
def _style_dataframe(df: pd.DataFrame) -> Any:
    """Apply a dark-themed style to the DataFrame for rich notebook display."""
    if df.empty:
        return df

    def _highlight_high_cpu(row: pd.Series) -> List[str]:
        """Highlight rows with high CPU usage in red."""
        if row["CPU"] > 80:
            return ["background-color: #8b0000; color: white"] * len(row)
        elif row["CPU"] > 50:
            return ["background-color: #b8860b; color: white"] * len(row)
        return [""] * len(row)

    styled = (
        df.style
        .apply(_highlight_high_cpu, axis=1)
        .format({"CPU": "{:.1f}%", "Memory": "{:.1f} MB"})
        .set_properties(**{
            "text-align": "center",
            "font-family": "Segoe UI, sans-serif",
            "font-size": "12px",
        })
        .set_table_styles([
            {"selector": "th", "props": [
                ("background-color", "#2b2b3c"),
                ("color", "white"),
                ("font-weight", "bold"),
                ("text-align", "center"),
                ("padding", "8px 12px"),
                ("font-family", "Segoe UI, sans-serif"),
            ]},
            {"selector": "td", "props": [
                ("padding", "6px 12px"),
            ]},
            {"selector": "table", "props": [
                ("border-collapse", "collapse"),
                ("width", "100%"),
            ]},
            {"selector": "caption", "props": [
                ("caption-side", "top"),
                ("font-size", "14px"),
                ("font-weight", "bold"),
                ("color", "#a0a0b0"),
                ("padding-bottom", "8px"),
            ]},
        ])
        .set_caption(
            f"Process Monitor — {datetime.now().strftime('%H:%M:%S')} "
            f"— {len(df)} processes"
        )
    )
    return styled


def display_processes() -> None:
    """Fetch, filter, sort, and display processes as a styled table.

    Uses ``IPython.display`` for rich output.  Falls back to ``print()``
    when not running inside IPython/Jupyter.
    """
    processes = fetch_processes()
    df = processes_to_dataframe(processes)
    df = filter_processes(df)
    df = sort_processes(df)

    if _HAS_IPYTHON:
        clear_output(wait=True)
        styled = _style_dataframe(df)
        display(styled)
    else:
        print(df.to_string(index=False))


# ── 6. Live Monitor Loop ─────────────────────────────────────────────
def live_monitor(interval: int = 3) -> None:
    """Continuously refresh the process table at *interval* seconds.

    Press **Interrupt Kernel** (⏹) in Jupyter to stop.

    Args:
        interval: Seconds between refreshes (default 3).
    """
    try:
        while True:
            display_processes()
            time.sleep(interval)
    except KeyboardInterrupt:
        if _HAS_IPYTHON:
            clear_output(wait=True)
        _safe_print("🛑 Live monitor stopped.")


# ── 7. Process Actions ───────────────────────────────────────────────
def kill_process(pid: int) -> bool:
    """Terminate a process by PID.

    Returns:
        ``True`` on success, ``False`` on failure.
    """
    try:
        result = _get_bridge().kill_process(pid)
        if result:
            _safe_print(f"✅ Process {pid} terminated successfully.")
        else:
            _safe_print(f"❌ Failed to terminate process {pid}.")
        return result
    except Exception as exc:
        _safe_print(f"❌ Error killing process {pid}: {exc}")
        return False


def pause_process(pid: int) -> bool:
    """Suspend a process by PID.

    Returns:
        ``True`` on success, ``False`` on failure.
    """
    try:
        result = _get_bridge().pause_process(pid)
        if result:
            _safe_print(f"⏸️ Process {pid} paused successfully.")
        else:
            _safe_print(f"❌ Failed to pause process {pid}.")
        return result
    except Exception as exc:
        _safe_print(f"❌ Error pausing process {pid}: {exc}")
        return False


def resume_process(pid: int) -> bool:
    """Resume a suspended process by PID.

    Returns:
        ``True`` on success, ``False`` on failure.
    """
    try:
        result = _get_bridge().resume_process(pid)
        if result:
            _safe_print(f"▶️ Process {pid} resumed successfully.")
        else:
            _safe_print(f"❌ Failed to resume process {pid}.")
        return result
    except Exception as exc:
        _safe_print(f"❌ Error resuming process {pid}: {exc}")
        return False


def set_priority(pid: int, value: int) -> bool:
    """Change a process's scheduling priority.

    Args:
        pid:   Target process ID.
        value: Priority adjustment (negative = higher priority).

    Returns:
        ``True`` on success, ``False`` on failure.
    """
    try:
        result = _get_bridge().change_priority(pid, value)
        if result:
            _safe_print(f"⚡ Priority of process {pid} changed to {value}.")
        else:
            _safe_print(f"❌ Failed to change priority for process {pid}.")
        return result
    except Exception as exc:
        _safe_print(f"❌ Error changing priority for process {pid}: {exc}")
        return False


# ── 8. CPU Usage Visualization ────────────────────────────────────────
# Internal storage for CPU history (survives across calls within one
# notebook session).
_cpu_history: List[float] = []
_cpu_timestamps: List[str] = []


def plot_cpu_usage(samples: int = 10, interval: float = 1.0) -> None:
    """Collect *samples* total-CPU readings and plot them as a line graph.

    Args:
        samples:  Number of data points to collect before plotting.
        interval: Seconds between each sample.
    """
    if not _HAS_MATPLOTLIB:
        _safe_print("⚠️  matplotlib is not installed. Run: pip install matplotlib")
        return

    global _cpu_history, _cpu_timestamps

    _safe_print(f"📊 Collecting {samples} CPU samples (interval={interval}s)…")

    for i in range(samples):
        processes = fetch_processes()
        total_cpu = sum(p.get("cpu", 0.0) for p in processes)
        _cpu_history.append(total_cpu)
        _cpu_timestamps.append(datetime.now().strftime("%H:%M:%S"))

        if _HAS_IPYTHON:
            clear_output(wait=True)
            _safe_print(f"📊 Collecting CPU samples… {i + 1}/{samples}")

        if i < samples - 1:
            time.sleep(interval)

    # Plot
    if _HAS_IPYTHON:
        clear_output(wait=True)

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(
        _cpu_timestamps[-samples:],
        _cpu_history[-samples:],
        marker="o",
        color="#00b4d8",
        linewidth=2,
        markersize=5,
        markerfacecolor="#0077b6",
    )
    ax.fill_between(
        range(len(_cpu_history[-samples:])),
        _cpu_history[-samples:],
        alpha=0.15,
        color="#00b4d8",
    )
    ax.set_facecolor("#1e1e2f")
    fig.patch.set_facecolor("#1e1e2f")
    ax.set_title("Total CPU Usage Over Time", color="white", fontsize=14, fontweight="bold")
    ax.set_xlabel("Time", color="#a0a0b0", fontsize=11)
    ax.set_ylabel("Total CPU %", color="#a0a0b0", fontsize=11)
    ax.tick_params(colors="#a0a0b0", labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#3c3c4e")
    ax.spines["bottom"].set_color("#3c3c4e")
    ax.grid(axis="y", color="#3c3c4e", linestyle="--", alpha=0.5)

    # Rotate x-axis labels to avoid overlap
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()


# ── 9. Bonus: Search ─────────────────────────────────────────────────
def search_process(name: str) -> pd.DataFrame:
    """Search for processes whose name contains *name* (case-insensitive).

    Returns a styled DataFrame when running in IPython, otherwise a
    plain DataFrame.
    """
    processes = fetch_processes()
    df = processes_to_dataframe(processes)

    if df.empty:
        _safe_print(f"⚠️  No processes found.")
        return df

    mask = df["Name"].str.contains(name, case=False, na=False)
    result = df[mask].reset_index(drop=True)

    if result.empty:
        _safe_print(f"🔍 No processes matching '{name}'.")
    else:
        _safe_print(f"🔍 Found {len(result)} process(es) matching '{name}':")
        if _HAS_IPYTHON:
            styled = _style_dataframe(result)
            display(styled)

    return result


# ── 10. Bonus: Export to CSV ──────────────────────────────────────────
def export_to_csv(filename: str = "processes_snapshot.csv") -> str:
    """Export the current (filtered, sorted) process snapshot to a CSV file.

    Args:
        filename: Output file path (default: ``processes_snapshot.csv``
                  in the current working directory).

    Returns:
        Absolute path to the written file.
    """
    processes = fetch_processes()
    df = processes_to_dataframe(processes)
    df = filter_processes(df)
    df = sort_processes(df)

    abs_path = os.path.abspath(filename)
    df.to_csv(abs_path, index=False)
    _safe_print(f"📁 Exported {len(df)} processes to: {abs_path}")
    return abs_path
