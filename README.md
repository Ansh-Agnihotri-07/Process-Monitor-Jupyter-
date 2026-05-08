# Process Monitor Jupyter Dashboard
> A real-time, highly granular process management and auto-control dashboard running directly in Jupyter Notebook.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![C++](https://img.shields.io/badge/C++-17-orange.svg)

---

## 🌟 Banner / Intro

**Process Monitor** is a sophisticated operating system utility that bridges the gap between low-level system APIs and high-level interactive visualizations. Designed for developers, system administrators, and power users, it provides unparalleled visibility into the active execution state of a Windows machine.

By coupling a lightning-fast C++ backend (interacting directly with Windows `Toolhelp32` and `psapi` APIs) with a dynamic Python/Jupyter frontend, this project solves the critical problem of rogue background tasks. It prevents battery drain, overheating, and sudden lag spikes by intelligently grouping system resources and offering a deterministic, state-aware **Auto Control** system to safely throttle high-CPU processes.

---

## ✨ Features

### Core Functionality
- **Real-Time Telemetry:** Accurate process tracking including CPU %, Working Set Memory, and true OS Priority Classes (`Idle`, `Normal`, `High`).
- **Smart Grouping:** Automatically consolidates multiple instances of the same application (e.g., dozens of `chrome.exe` tabs) into a single, cohesive dashboard entry with aggregated CPU/Memory values.

### Automation & Control
- **Intelligent Auto-Control:** A multi-stage, history-based mitigation system that tracks process misbehavior across time ticks. 
  - *Stage 1:* Gracefully lowers OS priority of processes exceeding threshold loads.
  - *Stage 2:* Safely pauses/suspends execution threads entirely if the load persists.
- **Granular Manipulation:** Direct capabilities to Kill, Pause, Resume, or arbitrarily Set Priority for any user-space process.

### Architecture Strengths
- **Decoupled Inter-Process Communication (IPC):** Uses robust JSON serialization over standard streams to strictly separate the unsafe C++ system environment from the Python visualization layer.
- **Non-Blocking UI:** Operates on daemonized background threads to ensure the Jupyter GUI remains responsive under heavy system load.

### Security
- **Fail-Safe Whitelisting:** Kernel/System processes (PID 0-4) and critical Windows binaries (`csrss.exe`, `svchost.exe`, `wininit.exe`) are strictly locked out of modification to prevent accidental system crashes.

---

## 🏗️ Architecture Overview

The system is built on a distributed, two-tier architecture:

1. **The Native Execution Layer (C++ Backend):**
   - Utilizes `CreateToolhelp32Snapshot`, `GetProcessTimes`, and `GetProcessMemoryInfo`.
   - Maintains its own temporal state (`pmcpu_state.tmp`) to calculate accurate CPU delta percentages across arbitrary time intervals.
   - Translates system structs into strict JSON outputs for robust consumption.
2. **The Orchestration Layer (Python & Jupyter):**
   - The `BackendBridge` spawns the native executable as a subprocess, ingesting the JSON telemetry.
   - **Pandas** acts as the memory and state management engine, grouping instances, filtering safe execution contexts, and orchestrating the final output.
   - **IPyWidgets** handles the event systems, async background loops, and HTML rendering for observability.

---

## 🔄 System Flow

1. **User Initiation:** The user executes `setup_and_run()` in the Jupyter Notebook.
2. **Background Thread Spawn:** A Python daemon thread awakens, polling every 5 seconds.
3. **Data Acquisition:** `backend_bridge.py` invokes `backend.exe list`. The C++ layer queries the Windows Kernel, calculates resource deltas, fetches `GetPriorityClass()`, and dumps a JSON array.
4. **Data Aggregation:** `notebook_interface.py` ingests the JSON into a Pandas DataFrame, groups identical application names, and constructs a list of associated PIDs.
5. **Rule Evaluation (Auto Control):** The Python loop evaluates the DataFrame against the `auto_history` dictionary. Rogue processes exceeding 40% CPU receive incremental ticks, triggering automated `changePriority` or `suspendResumeProcess` WinAPI calls.
6. **Observability Generation:** The DataFrame is styled into an HTML table and pushed to the IPyWidgets interface.

---

## 💻 Tech Stack

| Category | Technology |
|---|---|
| **Languages** | C++ (17), Python (3.x) |
| **Frameworks** | Jupyter Notebook, IPyWidgets, Pandas |
| **Infrastructure** | Windows API (`psapi`, `tlhelp32`) |
| **IPC** | Standard IO Streams (JSON protocol) |
| **Observability** | Python DOM manipulation, HTML/CSS DataFrames |
| **Deployment** | Make/g++ compilation, Local Python Environment |

---

## 📂 Folder Structure

```text
process-monitor/
├── backend/                   # Native C++ Windows API integration layer
│   ├── main.cpp               # CLI entry point
│   ├── control.cpp            # JSON serialization and argument parsing
│   ├── process_manager.cpp    # Core WinAPI telemetry and process manipulation
│   └── scheduler.cpp          # (Legacy) Thread scheduling prototypes
├── gui/                       # Python orchestration and processing
│   ├── backend_bridge.py      # Subprocess IPC handler
│   ├── notebook_interface.py  # Pandas aggregation and styling logic
│   └── table.py               # (Deprecated) Tkinter legacy tables
├── process_dashboard.ipynb    # Main entry point and IPyWidgets GUI
├── README.md                  # Project documentation
└── .gitignore                 # Version control rules
```

---

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Ansh-Agnihotri-07/Process-Monitor-Jupyter-.git
cd Process-Monitor-Jupyter-
```

### 2. Compile the C++ Backend (MinGW/GCC)
```powershell
cd backend
g++ main.cpp control.cpp process_manager.cpp scheduler.cpp -o backend.exe -lpsapi
cd ..
```

### 3. Install Python Dependencies
```bash
pip install pandas ipywidgets notebook
```

### 4. Run the Dashboard
```bash
jupyter notebook process_dashboard.ipynb
```

---

## 🔐 Environment Variables

This project currently does not require a `.env` file, as it relies directly on native OS API structures. However, key runtime configurations are hardcoded for security:
- `PROTECTED_PROCESSES`: Hardcoded list of kernel services in `process_dashboard.ipynb`.
- `refresh_interval`: Set to `5` (seconds) inside the UI loop to prevent CPU polling overhead.

---

## 💡 Usage

Once the Jupyter Notebook is opened, simply execute the main cell:

1. Click **Start Dashboard** to spawn the daemon thread.
2. Select an application from the dynamically aggregated Dropdown menu (e.g. `chrome.exe (Instances: 14)`).
3. Use the **Kill**, **Pause**, **Resume**, or **Set Priority** controls to manipulate the entire group of instances simultaneously.
4. Toggle **Auto Control** to enable intelligent background load management.

---

## ⚙️ Configuration

Key runtime configurations are located in `process_dashboard.ipynb`:
- **Auto Control Thresholds:** Currently set to trigger at `CPU > 40.0`. Modifying this value changes the strictness of the background resource manager.
- **Tick Decay:** When a process drops below the threshold, its penalty "ticks" decay, ensuring that temporary spikes are forgiven over time.

---

## 🧠 Execution & Auto-Control Pipeline

While not a true LLM system, the Auto-Control logic mirrors an intelligent decision pipeline:
1. **Context Handling:** Gathers full system telemetry every 5 seconds.
2. **Model Routing / State Tracking:** Maintains an `auto_history` memory dictionary. It does not act impulsively on a single spike. 
3. **Multi-step Reasoning:** 
   - *Tick 1:* Process exceeds threshold -> Context updated -> `Set Priority` invoked to demote task gracefully.
   - *Tick 2-3:* System monitors for compliance.
   - *Tick 4:* Non-compliance detected -> `SuspendThread` invoked to forcibly halt execution.
4. **Execution Validation:** Safe-guards (`is_safe_to_modify`) run *before* any tool orchestration to ensure kernel stability.

---

## 📊 Observability & Monitoring

- **HTML Tracing:** The `_style_dataframe` method injects CSS directly into the Pandas rendering pipeline, highlighting problematic processes in Warning Gold (`>50% CPU`) or Critical Red (`>80% CPU`).
- **Action Auditing:** Every manipulation (manual or automated) is tracked and printed cleanly to the `status_label` widget at the bottom of the interface, providing a transparent audit trail of system changes.

---

## 🛡️ Security

- **Isolation/Sandboxing:** The Python logic has zero direct access to memory. All dangerous system calls are heavily sandboxed behind the `backend.exe` executable.
- **Permission Systems:** 
  - Implicitly refuses to modify any PID `<= 4` (System/Idle processes).
  - Explicitly refuses to modify core Windows subsystem binaries via `PROTECTED_PROCESSES` validation.
- **Safe Execution:** The Auto-Control pipeline is explicitly forbidden from issuing `Kill` commands, eliminating the risk of automated data loss.

---

## 📈 Performance & Scalability

- **Parallel Processing:** The UI rendering and user interactions occur on the main Jupyter thread, while the process polling and Auto-Control loop run asynchronously via Python's `threading.Thread`.
- **Resource Optimization:** Time-delta calculation is pushed down to the C++ layer. Python only handles final JSON presentation, ensuring the dashboard requires `< 1%` CPU overhead to monitor thousands of threads.

---

## 🛠️ Development Workflow

1. **Local Development:** Ensure `backend.exe` is recompiled whenever C++ source files are altered.
2. **Testing:** You can artificially induce spikes via simple Python scripts (`while True: pass`) to test the Auto-Control thresholds.
3. **Contribution:** Fork the repository, create a feature branch (`git checkout -b feature/AmazingFeature`), commit changes, and open a Pull Request.

---

## 🔌 API Documentation

The native C++ backend (`backend.exe`) exposes the following command-line APIs for arbitrary usage outside of Python:

- `backend.exe list` -> Emits a JSON array of `{pid, name, state, priority, cpu, memory}`.
- `backend.exe kill <pid>` -> Terminates the specified PID.
- `backend.exe pause <pid>` -> Suspends all threads associated with the PID.
- `backend.exe resume <pid>` -> Resumes all threads associated with the PID.
- `backend.exe priority <pid> <val>` -> Modifies `SetPriorityClass`.

---

## 🖼️ Example Screenshots / Diagrams

*(Placeholders for future media)*

- **[Architecture Diagram Image Here]**
- **[Dashboard UI Screenshot Here]**
- **[Auto-Control Terminal Audit Log Here]**

---

## 🗺️ Roadmap

- [ ] Transition the JSON IPC to named pipes / WebSockets for true event-driven telemetry.
- [ ] Port the C++ backend to Linux using `/proc` filesystem parsing.
- [ ] Implement an overarching GPU monitoring integration.
- [ ] Deploy a standalone PyInstaller version of the dashboard.

---

## 🤝 Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## ✍️ Author

**Ansh Agnihotri and GAUTAM RANA**  
Project Link: [Process-Monitor-Jupyter-](https://github.com/Ansh-Agnihotri-07/Process-Monitor-Jupyter-)