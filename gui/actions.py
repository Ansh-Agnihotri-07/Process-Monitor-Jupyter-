import tkinter.messagebox as messagebox
from backend_bridge import kill_process, pause_process, resume_process, change_priority

# System processes that should never be killed or paused
PROTECTED_PROCESSES = {
    "system", 
    "svchost.exe", 
    "csrss.exe", 
    "wininit.exe", 
    "services.exe", 
    "smss.exe", 
    "lsass.exe",
    "explorer.exe" # added for safety
}

def is_safe_to_modify(pid, name):
    """Checks if a process is safe to pause/resume/kill."""
    if pid <= 4:
        return False
    if name.lower() in PROTECTED_PROCESSES:
        return False
    return True

def perform_kill(pid, name, on_success):
    """Attempt to kill the process with safety checks."""
    if not is_safe_to_modify(pid, name):
        messagebox.showwarning("Action Blocked", f"Cannot kill critical system process:\n{name} (PID: {pid})")
        return
        
    if messagebox.askyesno("Confirm Kill", f"Are you sure you want to terminate {name} (PID: {pid})?"):
        success = kill_process(pid)
        if success:
            on_success()
        else:
            messagebox.showerror("Error", f"Failed to kill process {name} ({pid}).")

def perform_pause(pid, name, on_success):
    """Attempt to pause the process with safety checks."""
    if not is_safe_to_modify(pid, name):
        messagebox.showwarning("Action Blocked", f"Cannot pause critical system process:\n{name} (PID: {pid})")
        return
        
    success = pause_process(pid)
    if success:
        on_success()
    else:
        messagebox.showerror("Error", f"Failed to pause process {name} ({pid}).")

def perform_resume(pid, name, on_success):
    """Attempt to resume a paused process."""
    if not is_safe_to_modify(pid, name):
        # We might block this as well just in case, though resuming is usually safe
        messagebox.showwarning("Action Blocked", f"Cannot modify critical system process:\n{name} (PID: {pid})")
        return
        
    success = resume_process(pid)
    if success:
        on_success()
    else:
        messagebox.showerror("Error", f"Failed to resume process {name} ({pid}).")

def perform_priority(pid, name, value, on_success):
    """Attempt to change process priority."""
    if not is_safe_to_modify(pid, name):
        messagebox.showwarning("Action Blocked", f"Cannot modify priority of critical system process:\n{name} (PID: {pid})")
        return
        
    success = change_priority(pid, value)
    if success:
        on_success()
    else:
        messagebox.showerror("Error", f"Failed to change priority for process {name} ({pid}).")
