import tkinter as tk
from tkinter import ttk, scrolledtext
import logging

class AppUI:
    """The main user interface for the Py2WinPro application."""

    def __init__(self, root: tk.Tk, product_name: str):
        self.root = root
        self.product_name = product_name
        self.root.title(f"{self.product_name} - Control Panel")
        self.root.geometry("800x600")

        # --- Main Frame ---
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Log Viewer ---
        log_frame = ttk.LabelFrame(main_frame, text="Application Logs", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_viewer = scrolledtext.ScrolledText(log_frame, state="disabled", wrap=tk.WORD, height=20)
        self.log_viewer.pack(fill=tk.BOTH, expand=True)

        # --- Controls ---
        controls_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        controls_frame.pack(fill=tk.X, pady=5)

        self.test_crash_button = ttk.Button(
            controls_frame,
            text="Test Crash",
            command=self._test_crash,
        )
        self.test_crash_button.pack(side=tk.LEFT, padx=5)

        self.clear_cache_button = ttk.Button(
            controls_frame,
            text="Clear Cache",
            command=self._clear_cache,
        )
        self.clear_cache_button.pack(side=tk.LEFT, padx=5)

        self.quit_button = ttk.Button(
            controls_frame,
            text="Quit",
            command=self.root.quit,
        )
        self.quit_button.pack(side=tk.RIGHT, padx=5)

        # --- Status Bar ---
        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _test_crash(self):
        """Intentionally raises an exception to test the crash handler."""
        logging.getLogger(self.product_name).info("Test crash button clicked.")
        raise ValueError("This is a test crash triggered by the user.")

    def _clear_cache(self):
        """Clears the application cache and updates the status bar."""
        from .crash_guard import _clear_cache
        self.update_status("Clearing cache...")
        if _clear_cache(self.product_name):
            self.update_status("Cache cleared successfully.")
        else:
            self.update_status("Failed to clear cache.")

    def update_log(self, message: str):
        """Appends a message to the log viewer."""
        self.log_viewer.configure(state="normal")
        self.log_viewer.insert(tk.END, message)
        self.log_viewer.configure(state="disabled")
        self.log_viewer.see(tk.END)

    def update_status(self, message: str):
        """Updates the status bar text."""
        self.status_bar.config(text=message)