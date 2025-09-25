# main.py
import sys
import time
import logging
import tkinter as tk
from logging import Handler, LogRecord

# Resilience stack
from py2win.crash_guard import install_crash_guard
from py2win.debug_daemon import DebugDaemon, Heartbeat
from py2win.preflight import run_preflight
from py2win.ui import AppUI

# SafeMode is optional; fall back to disabled if the module isn’t present yet.
try:
    from py2win.safe_mode import SafeMode
except ImportError:
    class SafeMode:
        @staticmethod
        def enabled() -> bool:
            return False

# --- Application Constants ---
APP_PRODUCT = "Py2WinPro"
APP_VERSION = "1.0.0"

class UILogHandler(Handler):
    """A custom logging handler that sends records to the UI."""
    def __init__(self, ui: AppUI):
        super().__init__()
        self.ui = ui

    def emit(self, record: LogRecord):
        msg = self.format(record)
        self.ui.update_log(msg + "\n")

def app_main() -> None:
    """Main application logic: sets up and runs the GUI event loop."""
    logger = logging.getLogger(APP_PRODUCT)
    logger.info("Main application loop starting.")

    # --- GUI Setup ---
    root = tk.Tk()
    ui = AppUI(root, APP_PRODUCT)

    # --- Logging to UI ---
    ui_handler = UILogHandler(ui)
    ui_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(ui_handler)

    # --- Watchdog and Heartbeat ---
    heartbeat = Heartbeat()
    debug_daemon = DebugDaemon(heartbeat_probe=heartbeat)
    debug_daemon.start()

    # --- Heartbeat Integration with Tkinter's Event Loop ---
    def heartbeat_tick():
        heartbeat.beat()
        root.after(2000, heartbeat_tick)  # Send a beat every 2 seconds

    root.after(1000, heartbeat_tick)  # Start the heartbeat after 1 second

    # --- Start the GUI ---
    logger.info("Starting GUI event loop.")
    root.mainloop()

    # --- Shutdown ---
    logger.info("Shutdown signal received. Exiting gracefully.")
    if debug_daemon.is_alive():
        debug_daemon.stop()
        debug_daemon.join(timeout=3)
    logger.info("Shutdown complete.")


def main() -> None:
    """
    Program entry point:
    1) initialize CrashGuard,
    2) honor Safe Mode,
    3) run pre-flight checks,
    4) start app loop.
    """
    # Console logger (CrashGuard adds file handler)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 1) Global exception handler and file logging
    install_crash_guard(app_version=APP_VERSION, product=APP_PRODUCT)

    # 2) Safe Mode (optional)
    if SafeMode.enabled():
        logging.getLogger(APP_PRODUCT).warning(
            "Launching in SAFE MODE. Some features may be disabled."
        )

    # 3) Pre-flight environment validation
    if not run_preflight(product_name=APP_PRODUCT):
        # Specific code for pre-flight failure so CI/scripts can detect it
        sys.exit(2)

    # 4) Start main application
    app_main()


if __name__ == "__main__":
    main()
