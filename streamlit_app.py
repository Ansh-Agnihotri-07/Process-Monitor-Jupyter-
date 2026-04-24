# -*- coding: utf-8 -*-
"""
streamlit_app.py — Modern Web Dashboard for Process Monitor.

A real-time process monitoring dashboard built with Streamlit that
reuses the existing C++ backend via backend_bridge.py.

Run with:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

import streamlit as st
import pandas as pd

# ---------------------------------------------------------------------------
# Path setup — ensure gui/ and its parent are importable regardless of CWD
# ---------------------------------------------------------------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_GUI_DIR = os.path.join(_THIS_DIR, "gui")

if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)
if _GUI_DIR not in sys.path:
    sys.path.insert(0, _GUI_DIR)

from backend_bridge import BackendBridge  # noqa: E402

# ---------------------------------------------------------------------------
# Page configuration — MUST be first Streamlit command
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Process Monitor",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for a premium dark monitoring-tool aesthetic
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* ── Global ────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    }

    /* ── Header ────────────────────────────────────────────────── */
    .dashboard-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    .dashboard-header h1 {
        background: linear-gradient(135deg, #00b4d8, #0077b6, #90e0ef);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .dashboard-header p {
        color: #7a7a9a;
        font-size: 0.9rem;
        margin: 0.25rem 0 0 0;
    }

    /* ── Metric cards ──────────────────────────────────────────── */
    .metric-card {
        background: linear-gradient(135deg, #1e1e2f 0%, #252540 100%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 180, 216, 0.15);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00b4d8, #90e0ef);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .metric-label {
        color: #7a7a9a;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 0.3rem 0 0 0;
    }

    /* ── Sidebar ───────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #12121f 0%, #1a1a2e 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
    section[data-testid="stSidebar"] .stMarkdown h2 {
        color: #00b4d8;
        font-size: 1.1rem;
        font-weight: 600;
        border-bottom: 1px solid rgba(0, 180, 216, 0.2);
        padding-bottom: 0.5rem;
    }

    /* ── Buttons ───────────────────────────────────────────────── */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.3px;
        transition: all 0.2s ease;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* ── Status badge ──────────────────────────────────────────── */
    .status-badge {
        display: inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .status-live {
        background: rgba(0, 200, 83, 0.15);
        color: #00c853;
        border: 1px solid rgba(0, 200, 83, 0.3);
    }
    .status-paused {
        background: rgba(255, 183, 0, 0.15);
        color: #ffb700;
        border: 1px solid rgba(255, 183, 0, 0.3);
    }

    /* ── Toast messages ────────────────────────────────────────── */
    .action-success {
        background: rgba(0, 200, 83, 0.1);
        border: 1px solid rgba(0, 200, 83, 0.3);
        border-radius: 8px;
        padding: 0.8rem 1rem;
        color: #00c853;
        font-weight: 500;
    }
    .action-error {
        background: rgba(255, 61, 71, 0.1);
        border: 1px solid rgba(255, 61, 71, 0.3);
        border-radius: 8px;
        padding: 0.8rem 1rem;
        color: #ff3d47;
        font-weight: 500;
    }

    /* ── Dataframe styling ─────────────────────────────────────── */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* ── Dividers ──────────────────────────────────────────────── */
    hr {
        border-color: rgba(255, 255, 255, 0.06) !important;
    }

    /* ── Hide default Streamlit branding ───────────────────────── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "bridge" not in st.session_state:
    st.session_state.bridge = BackendBridge()

if "cpu_history" not in st.session_state:
    st.session_state.cpu_history = []
    st.session_state.cpu_timestamps = []

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

if "refresh_interval" not in st.session_state:
    st.session_state.refresh_interval = 3

if "action_message" not in st.session_state:
    st.session_state.action_message = None

if "auto_control" not in st.session_state:
    st.session_state.auto_control = False

if "auto_control_kill" not in st.session_state:
    st.session_state.auto_control_kill = False

if "auto_control_cooldowns" not in st.session_state:
    st.session_state.auto_control_cooldowns = {}  # PID -> last action timestamp

# Protected system processes
PROTECTED_PROCESSES = {
    "system", "svchost.exe", "csrss.exe", "wininit.exe",
    "services.exe", "smss.exe", "lsass.exe", "explorer.exe",
}
CURRENT_PID = os.getpid()

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def fetch_processes() -> List[Dict[str, Any]]:
    """Fetch process list from the C++ backend via BackendBridge."""
    try:
        return st.session_state.bridge.list_processes(show_all=True)
    except Exception:
        return []

def get_instance_counts(processes: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate the number of instances for each process name."""
    counts = {}
    for p in processes:
        name = p.get("name", "").lower()
        if name:
            counts[name] = counts.get(name, 0) + 1
    return counts

def to_dataframe(processes: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert raw process list to a display-ready DataFrame."""
    if not processes:
        return pd.DataFrame(columns=["PID", "Name", "Status", "CPU (%)", "Memory (MB)"])

    rows = []
    for p in processes:
        rows.append({
            "PID": int(p.get("pid", 0)),
            "Name": str(p.get("name", "")),
            "Status": str(p.get("state", "")),
            "CPU (%)": round(float(p.get("cpu", 0.0)), 1),
            "Memory (MB)": round(float(p.get("memory", 0.0)), 1),
        })
    return pd.DataFrame(rows)


def filter_and_sort(df: pd.DataFrame) -> pd.DataFrame:
    """Remove system/low-usage processes and sort by CPU descending."""
    if df.empty:
        return df
    # Remove system PIDs
    df = df[df["PID"] > 4]
    
    # Identify system processes
    def is_sys(row):
        return row["Name"].lower() in PROTECTED_PROCESSES or row["PID"] == CURRENT_PID
    
    is_system_mask = df.apply(is_sys, axis=1)
    
    # Remove low-usage (CPU < 0.1 AND Memory < 5) unless it's a non-system process with > 0 CPU
    low = (df["CPU (%)"] < 0.1) & (df["Memory (MB)"] < 5) & is_system_mask
    df = df[~low]
    
    # Sort by CPU descending
    df = df.sort_values("CPU (%)", ascending=False).reset_index(drop=True)
    return df


def is_safe_to_modify(pid: int, name: str) -> bool:
    """Check if a process is safe to kill/pause/resume."""
    if pid <= 4:
        return False
    if pid == CURRENT_PID:
        return False
    if name.lower() in PROTECTED_PROCESSES:
        return False
    return True


def do_action_verified(action: str, pid: int, name: str, priority_value: int = -5) -> None:
    """Execute a process action and verify the result."""
    if not is_safe_to_modify(pid, name):
        st.session_state.action_message = (
            "error",
            f"Cannot modify critical/system process: {name or 'Unknown'} (PID {pid})"
        )
        return

    bridge = st.session_state.bridge
    success = False
    label = action.capitalize()

    try:
        if action == "kill":
            success = bridge.kill_process(pid)
        elif action == "pause":
            success = bridge.pause_process(pid)
        elif action == "resume":
            success = bridge.resume_process(pid)
        elif action == "priority":
            success = bridge.change_priority(pid, priority_value)
            label = "Priority change"
    except Exception as exc:
        st.session_state.action_message = ("error", f"{label} failed: {exc}")
        return

    # Post-action verification
    bridge.invalidate_cache()
    if action == "kill":
        time.sleep(0.5) # Give OS a moment to terminate
        current_procs = fetch_processes()
        still_exists = any(int(p.get("pid", 0)) == pid for p in current_procs)
        
        if still_exists:
            st.session_state.action_message = (
                "error", f"Kill command sent, but {name} (PID {pid}) is still running. May require elevated privileges."
            )
        else:
            st.session_state.action_message = (
                "success", f"Successfully confirmed termination of {name} (PID {pid})."
            )
    else:
        if success:
            st.session_state.action_message = (
                "success", f"{label} succeeded for PID {pid} ({name})"
            )
        else:
            st.session_state.action_message = (
                "error", f"{label} failed for PID {pid} ({name})"
            )

def do_action_killname(name: str) -> None:
    """Execute a kill-by-name action and report results."""
    if not name:
        return
    
    # Check if the name itself is protected
    if not is_safe_to_modify(100, name): # Fake PID to pass the check, we just want to test the name
        st.session_state.action_message = (
            "error",
            f"Cannot mass-kill critical/system process: {name}"
        )
        return
        
    bridge = st.session_state.bridge
    try:
        result = bridge.kill_processes_by_name(name)
        killed = result.get("killed", 0)
        failed = result.get("failed", 0)
        
        # Verify
        bridge.invalidate_cache()
        time.sleep(0.5)
        current_procs = fetch_processes()
        instances_left = sum(1 for p in current_procs if str(p.get("name", "")).lower() == name.lower())
        
        if killed > 0 and instances_left == 0:
             st.session_state.action_message = (
                 "success", f"Successfully terminated all {killed} instances of {name}."
             )
        elif killed > 0 and instances_left > 0:
             st.session_state.action_message = (
                 "warning", f"Killed {killed} instances, but {instances_left} are still running (Failed to kill {failed})."
             )
        elif failed > 0:
             st.session_state.action_message = (
                 "error", f"Failed to kill {failed} instances of {name}. May require elevated privileges."
             )
        else:
             st.session_state.action_message = (
                 "info", f"No instances of {name} found to kill."
             )
             
    except Exception as exc:
        st.session_state.action_message = ("error", f"Kill All failed: {exc}")


def run_tiered_auto_control(df: pd.DataFrame) -> None:
    """Automatically manage high-CPU processes using a tiered approach."""
    if not st.session_state.auto_control or df.empty:
        return

    bridge = st.session_state.bridge
    actioned = []
    now = time.time()
    
    # Tiers
    PRIORITY_TIER = 20.0
    PAUSE_TIER = 40.0
    KILL_TIER = 70.0
    COOLDOWN_SEC = 10.0

    for _, row in df.iterrows():
        cpu = row["CPU (%)"]
        pid = int(row["PID"])
        name = str(row["Name"])
        
        if cpu > PRIORITY_TIER and is_safe_to_modify(pid, name):
            # Check cooldown
            last_action_time = st.session_state.auto_control_cooldowns.get(pid, 0)
            if now - last_action_time < COOLDOWN_SEC:
                continue
                
            try:
                acted = False
                if cpu > KILL_TIER and st.session_state.auto_control_kill:
                    if bridge.kill_process(pid):
                        actioned.append(f"Killed {name} ({pid})")
                        acted = True
                elif cpu > PAUSE_TIER:
                    if bridge.pause_process(pid):
                        actioned.append(f"Paused {name} ({pid})")
                        acted = True
                elif cpu > PRIORITY_TIER:
                    if bridge.change_priority(pid, 10): # Lower priority (higher nice value)
                        actioned.append(f"Lowered Priority {name} ({pid})")
                        acted = True
                        
                if acted:
                    st.session_state.auto_control_cooldowns[pid] = now
            except Exception:
                pass

    if actioned:
        st.session_state.action_message = (
            "warning",
            f"Auto-control triggered for {len(actioned)} process(es): {', '.join(actioned[:5])}"
        )


# ---------------------------------------------------------------------------
# Fetch data
# ---------------------------------------------------------------------------
raw_processes = fetch_processes()
instance_counts = get_instance_counts(raw_processes)
df_all = to_dataframe(raw_processes)
df = filter_and_sort(df_all)

# Track CPU history
total_cpu = df["CPU (%)"].sum() if not df.empty else 0.0
st.session_state.cpu_history.append(total_cpu)
st.session_state.cpu_timestamps.append(datetime.now().strftime("%H:%M:%S"))

# Keep last 60 data points
if len(st.session_state.cpu_history) > 60:
    st.session_state.cpu_history = st.session_state.cpu_history[-60:]
    st.session_state.cpu_timestamps = st.session_state.cpu_timestamps[-60:]

# Run auto control if enabled
run_tiered_auto_control(df)


# ---------------------------------------------------------------------------
# ─── SIDEBAR ──────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🔧 Controls")

    # ── Refresh settings ─────────────────────────────────────────
    st.session_state.auto_refresh = st.toggle(
        "Auto Refresh", value=st.session_state.auto_refresh
    )
    st.session_state.refresh_interval = st.slider(
        "Refresh interval (s)", min_value=1, max_value=10,
        value=st.session_state.refresh_interval,
    )

    if st.button("🔄 Refresh Now", width="stretch"):
        st.session_state.bridge.invalidate_cache()
        st.rerun()

    st.divider()

    # ── Process actions ──────────────────────────────────────────
    st.markdown("## ⚡ Process Actions")

    # Process Selection Dropdown
    process_options = [{"label": "Select a process...", "pid": 0, "name": ""}]
    for _, row in df.iterrows():
        pid = int(row["PID"])
        name = str(row["Name"])
        cpu = row["CPU (%)"]
        count = instance_counts.get(name.lower(), 1)
        safe = is_safe_to_modify(pid, name)
        
        icon = "⚠️ " if not safe else ""
        label = f"{icon}{name} (PID {pid}) — CPU {cpu}% [{count} instances]"
        process_options.append({"label": label, "pid": pid, "name": name})

    selected_option = st.selectbox(
        "Target Process",
        options=process_options,
        format_func=lambda x: x["label"],
        help="Select a process from the list to manage it."
    )
    
    target_pid = selected_option["pid"]
    target_name = selected_option["name"]
    buttons_disabled = target_pid == 0

    col_k, col_p, col_r = st.columns(3)
    with col_k:
        if st.button("🗑 Kill", width="stretch", type="primary", disabled=buttons_disabled):
            do_action_verified("kill", target_pid, target_name)
            st.rerun()
    with col_p:
        if st.button("⏸ Pause", width="stretch", disabled=buttons_disabled):
            do_action_verified("pause", target_pid, target_name)
            st.rerun()
    with col_r:
        if st.button("▶ Resume", width="stretch", disabled=buttons_disabled):
            do_action_verified("resume", target_pid, target_name)
            st.rerun()

    if st.button(f"💀 Kill All {target_name if target_name else 'Instances'}", width="stretch", type="primary", disabled=buttons_disabled):
        do_action_killname(target_name)
        st.rerun()

    priority_val = st.slider(
        "Priority value", min_value=-20, max_value=19, value=-5,
        help="Lower value = higher priority",
        disabled=buttons_disabled
    )
    if st.button("⚡ Set Priority", width="stretch", disabled=buttons_disabled):
        do_action_verified("priority", target_pid, target_name, priority_val)
        st.rerun()

    st.divider()

    # ── Auto control ─────────────────────────────────────────────
    st.markdown("## 🤖 Auto Control")
    st.session_state.auto_control = st.toggle(
        "Enable Tiered Auto-Control", value=st.session_state.auto_control,
        help="Automatically lower priority (>20% CPU), pause (>40%), or kill (>70%). 10s cooldown per PID."
    )
    st.session_state.auto_control_kill = st.checkbox(
        "Allow Aggressive Kill (>70% CPU)", value=st.session_state.auto_control_kill,
        disabled=not st.session_state.auto_control,
        help="If checked, processes sustaining >70% CPU will be terminated automatically."
    )

    st.divider()

    # ── Backend status ───────────────────────────────────────────
    st.markdown("## 📡 Backend")
    if st.session_state.bridge.is_available:
        st.markdown(
            '<span class="status-badge status-live">● CONNECTED</span>',
            unsafe_allow_html=True,
        )
        st.caption(f"`{st.session_state.bridge.backend_path}`")
    else:
        st.markdown(
            '<span class="status-badge status-paused">● OFFLINE</span>',
            unsafe_allow_html=True,
        )
        st.error("backend.exe not found!")


# ---------------------------------------------------------------------------
# ─── MAIN CONTENT ─────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

# ── Header ───────────────────────────────────────────────────────────
st.markdown("""
<div class="dashboard-header">
    <h1>⚙️ Process Monitor Dashboard</h1>
    <p>Real-time system process monitoring &amp; control</p>
</div>
""", unsafe_allow_html=True)

# ── Action message toast ─────────────────────────────────────────────
if st.session_state.action_message:
    msg_type, msg_text = st.session_state.action_message
    if msg_type == "success":
        st.success(msg_text, icon="✅")
    elif msg_type == "warning":
        st.warning(msg_text, icon="⚠️")
    elif msg_type == "info":
        st.info(msg_text, icon="ℹ️")
    else:
        st.error(msg_text, icon="❌")
    st.session_state.action_message = None

# ── Metric cards ─────────────────────────────────────────────────────
now_str = datetime.now().strftime("%H:%M:%S")
total_procs = len(df)
avg_cpu = df["CPU (%)"].mean() if not df.empty else 0.0
total_mem = df["Memory (MB)"].sum() if not df.empty else 0.0
high_cpu_count = len(df[df["CPU (%)"] > 50]) if not df.empty else 0

mc1, mc2, mc3, mc4, mc5 = st.columns(5)

with mc1:
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{total_procs}</p>
        <p class="metric-label">Active Processes</p>
    </div>
    """, unsafe_allow_html=True)

with mc2:
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{total_cpu:.1f}%</p>
        <p class="metric-label">Total CPU</p>
    </div>
    """, unsafe_allow_html=True)

with mc3:
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{avg_cpu:.1f}%</p>
        <p class="metric-label">Avg CPU / Process</p>
    </div>
    """, unsafe_allow_html=True)

with mc4:
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value">{total_mem:,.0f}</p>
        <p class="metric-label">Total Memory (MB)</p>
    </div>
    """, unsafe_allow_html=True)

with mc5:
    st.markdown(f"""
    <div class="metric-card">
        <p class="metric-value" style="color: {'#ff3d47' if high_cpu_count > 0 else '#00c853'};">
            {high_cpu_count}
        </p>
        <p class="metric-label">High CPU ({'>'}50%)</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Process table + CPU chart ────────────────────────────────────────
tab_table, tab_chart = st.tabs(["📋 Process Table", "📊 CPU Trend"])

with tab_table:
    if df.empty:
        st.warning("No process data available. Is backend.exe running?")
    else:
        # Search filter
        search = st.text_input(
            "🔍 Search processes", placeholder="Type to filter by name…",
            label_visibility="collapsed",
        )
        display_df = df.copy()
        if search:
            display_df = display_df[
                display_df["Name"].str.contains(search, case=False, na=False)
            ].reset_index(drop=True)

        # Highlight logic
        def highlight_row(row: pd.Series) -> list[str]:
            cpu = row["CPU (%)"]
            pid = row["PID"]
            
            # Highlight selected process
            if pid == target_pid:
                return ["background-color: rgba(0, 180, 216, 0.3); border: 1px solid #00b4d8; color: #fff"] * len(row)
                
            # Highlight high CPU
            if cpu > 80:
                return ["background-color: rgba(255,61,71,0.25); color: #ff6b6b"] * len(row)
            elif cpu > 50:
                return ["background-color: rgba(255,183,0,0.2); color: #ffd666"] * len(row)
            return [""] * len(row)

        styled = (
            display_df.style
            .apply(highlight_row, axis=1)
            .format({"CPU (%)": "{:.1f}", "Memory (MB)": "{:.1f}"})
        )

        st.dataframe(
            styled,
            width="stretch", # Fixing deprecation warning
            height=500,
            column_config={
                "PID": st.column_config.NumberColumn("PID", format="%d", width="small"),
                "Name": st.column_config.TextColumn("Name", width="large"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "CPU (%)": st.column_config.ProgressColumn(
                    "CPU (%)", min_value=0, max_value=100, format="%.1f%%",
                    width="medium",
                ),
                "Memory (MB)": st.column_config.NumberColumn(
                    "Memory (MB)", format="%.1f MB", width="medium",
                ),
            },
        )

        st.caption(
            f"Showing {len(display_df)} of {len(df)} processes · "
            f"Last updated: {now_str}"
        )

with tab_chart:
    if len(st.session_state.cpu_history) > 1:
        chart_df = pd.DataFrame({
            "Time": st.session_state.cpu_timestamps,
            "Total CPU (%)": st.session_state.cpu_history,
        })
        st.line_chart(
            chart_df.set_index("Time"),
            width="stretch", # Fixing deprecation warning
            height=350,
        )
        st.caption(
            f"Tracking {len(st.session_state.cpu_history)} data points "
            f"({st.session_state.refresh_interval}s interval)"
        )
    else:
        st.info("CPU trend data will appear after a few refresh cycles.")

# ── Footer ───────────────────────────────────────────────────────────
st.markdown(
    f"<div style='text-align:center; color:#4a4a6a; font-size:0.75rem; "
    f"padding:2rem 0 1rem 0;'>"
    f"Process Monitor Dashboard · Updated {now_str} · "
    f"Refresh {'ON' if st.session_state.auto_refresh else 'OFF'} "
    f"({st.session_state.refresh_interval}s)"
    f"</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Auto-refresh loop
# ---------------------------------------------------------------------------
if st.session_state.auto_refresh:
    time.sleep(st.session_state.refresh_interval)
    st.rerun()
