import sys
import json
import traceback
import time
import os
import logging
from logging.handlers import RotatingFileHandler

# Define the application name and log directory
APP_NAME = "Py2WinPro"
LOG_DIR = os.path.join(os.path.expanduser("~"), f".{APP_NAME.lower()}", "logs")

# Ensure the log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Set up the main application logger
logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.INFO)
# Prevent logging from propagating to the root logger to avoid duplicate outputs
logger.propagate = False

# Create a rotating file handler and formatter
handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "app.log"), maxBytes=2_000_000, backupCount=5
)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger only if it hasn't been added before
if not logger.handlers:
    logger.addHandler(handler)

def _generate_crash_report(exc_type, exc_value, tb):
    """Generates a detailed JSON crash report."""
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "exc_type": exc_type.__name__,
        "message": str(exc_value),
        "traceback": ''.join(traceback.format_tb(tb)),
        "version": "1.0.0",  # Placeholder for app version
        "platform": sys.platform,
        "app_name": APP_NAME,
    }

    # Save the report to a file with a unique timestamp
    crash_report_path = os.path.join(LOG_DIR, f"crash_{int(time.time())}.json")
    try:
        with open(crash_report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return crash_report_path
    except IOError as e:
        # Log an error if the report can't be written
        logger.error("Failed to write crash report to %s: %s", crash_report_path, e)
        return None

def _attempt_self_heal():
    """A placeholder for future self-healing logic."""
    try:
        # Future logic could include disabling plugins, resetting caches, etc.
        logger.info("Entering Safe Mode and attempting self-heal.")
    except Exception as e:
        logger.exception("Self-heal attempt failed: %s", e)

def _crash_handler(exc_type, exc_value, tb):
    """
    The main crash handler function assigned to sys.excepthook.
    It logs the error, generates a report, and attempts to self-heal.
    """
    # Log the critical error with full exception info
    logger.critical("Unhandled exception caught!", exc_info=(exc_type, exc_value, tb))

    # Generate and save the detailed crash report
    report_path = _generate_crash_report(exc_type, exc_value, tb)
    if report_path:
        logger.error("Crash report saved to: %s", report_path)

    # Trigger the self-heal process
    _attempt_self_heal()

    # For a real app, you might show a user-friendly dialog here.
    # For now, we print to stderr to notify the user.
    print(f"A critical error occurred. A crash report has been saved to {report_path}", file=sys.stderr)

def setup_crash_guard():
    """
    Initializes the crash guard and logging system.
    This should be called once when the application starts.
    """
    sys.excepthook = _crash_handler
    logger.info("CrashGuard initialized. Unhandled exceptions will now be caught.")
