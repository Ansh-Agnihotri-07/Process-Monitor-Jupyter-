import tkinter as tk
from tkinter import ttk

class ProcessTable(ttk.Treeview):
    def __init__(self, parent):
        columns = ("PID", "Name", "Status", "CPU", "Memory")
        super().__init__(parent, columns=columns, show="headings", selectmode="browse")
        
        # Style Configuration
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                        background="#2b2b2b", 
                        foreground="#ffffff",
                        fieldbackground="#2b2b2b", 
                        rowheight=30, 
                        font=("Segoe UI", 10))
        
        style.configure("Treeview.Heading", 
                        background="#3c3f41", 
                        foreground="#ffffff", 
                        font=("Segoe UI", 10, "bold"),
                        padding=5)
                        
        style.map("Treeview", background=[("selected", "#0078D7")])
        style.map("Treeview.Heading", background=[("active", "#4c5052")])
        
        # Determine column structure
        for col in columns:
            self.heading(col, text=col)
            # Make the Name column slightly wider
            width = 250 if col == "Name" else 100
            self.column(col, anchor=tk.CENTER, width=width)
            
        # Tags for row styles
        self.tag_configure("high_cpu", background="#8b0000", foreground="white") # red background
        self.tag_configure("even", background="#2b2b2b", foreground="white")
        self.tag_configure("odd", background="#323537", foreground="white")
        
        # Build Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.yview)
        self.configure(yscroll=scrollbar.set)
        
        # Layout
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.pack(fill=tk.BOTH, expand=True)

    def get_selected(self):
        """Returns the data of the currently selected row or None."""
        selection = self.selection()
        if not selection:
            return None
        item = self.item(selection[0])
        return item['values'] # e.g. [pid, name, status, cpu_str, mem_str]

    def update_data(self, processes, cpu_threshold=80.0):
        """Re-populates the treeview with the latest process data."""
        # Clear existing items
        self.delete(*self.get_children())
        
        # Insert current items
        for i, proc in enumerate(processes):
            pid = proc.get("pid", 0)
            name = proc.get("name", "")
            state = proc.get("state", "Unknown")
            cpu = proc.get("cpu", 0.0)
            mem = proc.get("memory", 0.0)
            
            tags = ()
            # Assign styling tags based on properties
            if cpu > cpu_threshold:
                tags = ("high_cpu",)
            elif i % 2 == 0:
                tags = ("even",)
            else:
                tags = ("odd",)
                
            self.insert("", tk.END, values=(
                pid, 
                name, 
                state, 
                f"{cpu:.1f}%", 
                f"{mem:.1f}%"
            ), tags=tags)
