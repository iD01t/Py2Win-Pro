import sys
import json
import traceback
import time
import os
import logging
from logging.handlers import RotatingFileHandler

def _get_data_dir(product_name: str) -> str:
    """Gets the application's user data directory path based on OS."""
    if sys.platform == "win32":
        return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), product_name)
    # Fallback for other OSes (e.g., for testing in Linux sandbox)
    return os.path.join(os.path.expanduser("~"), f".{product_name.lower()}")

def _generate_crash_report(exc_type, exc_value, tb, app_version, product, data_dir):
    """Generates a detailed JSON crash report in the 'crashes' subdirectory."""
    logger = logging.getLogger(product)
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "exc_type": exc_type.__name__,
        "message": str(exc_value),
        "traceback": ''.join(traceback.format_tb(tb)),
        "version": app_version,
        "platform": sys.platform,
        "product": product,
    }

    crash_dir = os.path.join(data_dir, "crashes")
    os.makedirs(crash_dir, exist_ok=True)

    crash_report_path = os.path.join(crash_dir, f"crash_{int(time.time())}.json")
    try:
        with open(crash_report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return crash_report_path
    except IOError as e:
        logger.error("Failed to write crash report to %s: %s", crash_report_path, e)
        return None

def _attempt_self_heal(product: str):
    """A placeholder for future self-healing logic."""
    logger = logging.getLogger(product)
    try:
        logger.info("Attempting self-heal...")
        # In the future, this could trigger a restart in safe mode.
    except Exception as e:
        logger.exception("Self-heal attempt failed: %s", e)

def install_crash_guard(app_version: str, product: str):
    """
    Initializes the crash guard and logging system. This should be called
    once at application startup.
    """
    data_dir = _get_data_dir(product)
    log_dir = os.path.join(data_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Set up the main application logger
    logger = logging.getLogger(product)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Add a handler only if one doesn't exist to prevent duplication
    if not logger.handlers:
        handler = RotatingFileHandler(
            os.path.join(log_dir, "app.log"), maxBytes=2_000_000, backupCount=5
        )
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    def crash_handler(exc_type, exc_value, tb):
        """The actual function that gets assigned to sys.excepthook."""
        # Log the crash first
        logger.critical("Unhandled exception caught!", exc_info=(exc_type, exc_value, tb))

        # Generate the report
        report_path = _generate_crash_report(exc_type, exc_value, tb, app_version, product, data_dir)
        if report_path:
            logger.error("Crash report saved to: %s", report_path)

        # Attempt to heal
        _attempt_self_heal(product)

        # Notify the user (in a console app, this prints to stderr)
        print(f"\nA critical error occurred in {product}.", file=sys.stderr)
        print(f"A crash report has been saved to: {report_path}", file=sys.stderr)
        # TODO: Offer to restart in Safe Mode.

    sys.excepthook = crash_handler
    logger.info("CrashGuard initialized for %s v%s.", product, app_version)
    logger.info("User data directory is: %s", data_dir)
