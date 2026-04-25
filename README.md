# Process Monitor

## About the Project
Process Monitor is an operating systems project I built to learn more about how systems manage active processes. It provides a visual dashboard to monitor running processes, CPU usage, and system data. 

The project is split into two parts: a C++ backend that interacts directly with system APIs to fetch process data, and a Python GUI built with Tkinter that displays this data in a readable way. It's a relatively simple implementation, but it helped me understand the bridge between low-level system calls and user-facing applications.

## Features
- **Process List:** View a table of currently running processes and basic memory/CPU stats.
- **System Monitoring:** A dashboard to monitor system usage over time.
- **Process Control:** Basic controls to suspend, resume, or terminate a specific process.
- **Logging:** Automatically logs significant process events and errors.

## How It Works

The project relies on communication between two different languages:

1. **The C++ Backend:** This program handles the actual system calls. It gathers data about active processes, handles the process scheduling logic, and directly executes commands like killing a process.
2. **The Python GUI:** This is the interface the user interacts with. It's an event-driven Tkinter app that provides a table, buttons, and visualizations.
3. **Communication Bridge:** The Python application starts the C++ backend as a subprocess. The backend writes its data (like process lists) to standard output (or a file), which the Python application then reads, parses, and updates on the GUI. When you click "Kill" in the Python GUI, it sends a command to the C++ backend to handle the actual OS-level termination.

## Project Structure
```text
process-monitor/
├── backend/          # Contains all C++ code for system calls and logic
├── gui/              # Contains the Python Tkinter interface (app.py)
├── logs/             # Where event logs are saved when the app runs
└── README.md         # This file
```

## Setup Instructions

You'll need a C++ compiler and Python installed on your machine.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/process-monitor.git
   cd process-monitor
   ```

2. **Compile the C++ code:**
   Navigate into the repository and compile the backend.
   ```bash
   g++ -std=c++17 backend/main.cpp backend/process_manager.cpp -o process-monitor-backend
   ```
   *(Note: Adjust the file names based on the specific C++ files in the backend folder.)*

3. **Python Requirements:**
   The GUI uses standard Python libraries, so you shouldn't need to install anything extra via pip. Just make sure you have Tkinter installed (it comes with Python by default on Windows/macOS, but might need `sudo apt install python3-tk` on Linux).

## How to Run

1. Make sure you have compiled the backend into the executable `process-monitor-backend`.
2. Run the Python application from the root folder:
   ```bash
   python gui/app.py
   ```
3. The GUI will open, automatically start the backend, and begin displaying your process data.

## Limitations
- **Platform Dependency:** Some of the C++ system calls might be tailored specifically to Windows or Linux. It might not work perfectly across all operating systems without modification.
- **Efficiency:** The Python GUI continuously polls the backend for updates, which could consume a bit of CPU itself if refreshed too often.
- **Basic GUI:** The interface is built with standard Tkinter, so it's functional but lacks advanced graphical features.

## Future Improvements
- Refactoring the IPC (Inter-Process Communication) to use sockets or pipes instead of basic standard output polling to make it more reliable.
- Adding a search bar to easily find specific processes.
- Making the C++ API calls completely cross-platform.