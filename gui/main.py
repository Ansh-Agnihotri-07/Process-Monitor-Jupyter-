import tkinter as tk
from app import MainApp

def main():
    root = tk.Tk()
    
    # Configure root window properties
    root.title("Process Monitor")
    
    # Optional: If there's an icon, we could set it here
    # root.iconbitmap("app_icon.ico")
    
    # Initialize the main application
    app = MainApp(root)
    
    # Start the Tkinter main event loop
    root.mainloop()

if __name__ == "__main__":
    main()
