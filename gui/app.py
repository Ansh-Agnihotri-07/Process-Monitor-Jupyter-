import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from table import ProcessTable
from actions import perform_kill, perform_pause, perform_resume, perform_priority, is_safe_to_modify
from backend_bridge import BackendBridge

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Process Monitor")
        self.root.geometry("850x650")
        self.root.configure(bg="#2b2b2b")
        
        # Instantiate the bridge (auto-detects backend.exe with dynamic paths)
        self.bridge = BackendBridge()
        
        # Application state
        self.auto_control_var = tk.BooleanVar(value=False)
        self.auto_control_threshold = 80.0
        # Determine the refresh rate (e.g. 3000 ms)
        self.refresh_interval = 3000 
        self.refresh_job_id = None
        
        self.setup_ui()
        
        # Start the refresh loop
        self.refresh_loop()

    def setup_ui(self):
        # 1. Top Frame: Status and Controls
        top_frame = tk.Frame(self.root, bg="#2b2b2b")
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        self.status_label = tk.Label(top_frame, text="Last Updated: Never", bg="#2b2b2b", fg="#ffffff", font=("Segoe UI", 10))
        self.status_label.pack(side=tk.LEFT)
        
        # Auto Control Toggle
        self.auto_chk = tk.Checkbutton(
            top_frame, 
            text="Auto Control (Pause High CPU): OFF", 
            variable=self.auto_control_var,
            command=self.on_auto_control_toggle, 
            bg="#2b2b2b", 
            fg="#ffffff", 
            selectcolor="#4c5052", 
            activebackground="#2b2b2b", 
            activeforeground="#ffffff",
            font=("Segoe UI", 10)
        )
        self.auto_chk.pack(side=tk.RIGHT)
        
        # 2. Middle Frame: Table
        mid_frame = tk.Frame(self.root, bg="#2b2b2b")
        mid_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10)
        
        self.table = ProcessTable(mid_frame)
        
        # 3. Bottom Frame: Action Buttons
        bot_frame = tk.Frame(self.root, bg="#2b2b2b")
        bot_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        btn_style = {
            "bg": "#0078D7", 
            "fg": "#ffffff", 
            "font": ("Segoe UI", 10, "bold"), 
            "relief": tk.FLAT, 
            "padx": 15, 
            "pady": 5,
            "activebackground": "#005a9e",
            "activeforeground": "#ffffff"
        }
        
        tk.Button(bot_frame, text="Kill", command=self.on_kill, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(bot_frame, text="Pause", command=self.on_pause, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(bot_frame, text="Resume", command=self.on_resume, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(bot_frame, text="Boost Priority", command=self.on_boost, **btn_style).pack(side=tk.LEFT, padx=5)

    def on_auto_control_toggle(self):
        """Update checkbox label based on variable state."""
        state = "ON" if self.auto_control_var.get() else "OFF"
        self.auto_chk.configure(text=f"Auto Control (Pause High CPU): {state}")

    def trigger_instant_refresh(self):
        """Called upon successful actions to refresh the UI immediately."""
        # Cancel the existing delayed refresh if any
        if self.refresh_job_id is not None:
            self.root.after_cancel(self.refresh_job_id)
            self.refresh_job_id = None
            
        # The backend bridge automatically invalidates its cache internally when
        # mutating actions (kill/pause/resume/priority) succeed. We can just
        # call the fetch data and refresh UI immediately.
        self.refresh_loop()

    # Button Event Handlers
    def on_kill(self):
        sel = self.table.get_selected()
        if sel:
            pid = sel[0]
            name = sel[1]
            perform_kill(pid, name, self.trigger_instant_refresh)
        else:
            messagebox.showinfo("Select Process", "Please select a process from the table first.")

    def on_pause(self):
        sel = self.table.get_selected()
        if sel:
            pid = sel[0]
            name = sel[1]
            perform_pause(pid, name, self.trigger_instant_refresh)
        else:
            messagebox.showinfo("Select Process", "Please select a process from the table first.")

    def on_resume(self):
        sel = self.table.get_selected()
        if sel:
            pid = sel[0]
            name = sel[1]
            perform_resume(pid, name, self.trigger_instant_refresh)
        else:
            messagebox.showinfo("Select Process", "Please select a process from the table first.")
            
    def on_boost(self):
        sel = self.table.get_selected()
        if sel:
            pid = sel[0]
            name = sel[1]
            # Lower value = higher priority. Decrementing by 5 up to OS limits.
            perform_priority(pid, name, -5, self.trigger_instant_refresh)
        else:
            messagebox.showinfo("Select Process", "Please select a process from the table first.")

    def run_auto_control(self, processes):
        """Scheduler simulation: Automatically pause unsafe high CPU processes."""
        if not self.auto_control_var.get():
            return
            
        for proc in processes:
            cpu = proc.get("cpu", 0.0)
            pid = proc.get("pid", 0)
            name = proc.get("name", "")
            
            if cpu > self.auto_control_threshold:
                if is_safe_to_modify(pid, name):
                    # We just log it visually and trigger the pause action via bridge
                    print(f"Auto Control: Scheduling pause for {name} ({pid}) with CPU {cpu}%")
                    # Using the Bridge's direct action rather than the MessageBox prompted one.
                    # This prevents the user from being bombarded with prompts during auto control
                    if self.bridge.pause_process(pid):
                        print(f"Auto Control: Successfully paused {name} ({pid})")

    def refresh_loop(self):
        """The main loop driven by Tkinter after() method."""
        # 1. Fetch real data from backend
        processes = self.bridge.list_processes()
        
        # 2. Run automatic scheduler logic
        if processes:
            self.run_auto_control(processes)
        
        # 3. Update the UI treeview
        self.table.update_data(processes, self.auto_control_threshold)
        
        # 4. Update status indicator
        now = datetime.now().strftime("%H:%M:%S")
        self.status_label.configure(text=f"Last Updated: {now}")
        
        # 5. Schedule next update safely
        self.refresh_job_id = self.root.after(self.refresh_interval, self.refresh_loop)
