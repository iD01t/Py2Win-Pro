# crash_guard.py
import sys
import json
import traceback
import time
import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

# Defaults (used by setup_crash_guard)
APP_NAME_DEFAULT = "Py2WinPro"
APP_VERSION_DEFAULT = "1.0.0"


# ---------------------------
# Paths
# ---------------------------
def _get_data_dir(product_name: str) -> str:
    """
    Return the per-user data directory for the product.
    Windows: %LOCALAPPDATA%\<Product>
    Others : ~/.<product>
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return os.path.join(base, product_name)
    return os.path.join(os.path.expanduser("~"), f".{product_name.lower()}")


# ---------------------------
# Crash report generation
# ---------------------------
def _get_system_info() -> dict:
    """Gather basic system information for the crash report."""
    import platform
    info = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
    }
    try:
        # psutil is a powerful library for system monitoring.
        # It's not a default dependency, so we handle its absence gracefully.
        import psutil
        info["cpu_count"] = psutil.cpu_count()
        info["memory_total_mb"] = psutil.virtual_memory().total // (1024 * 1024)
        info["memory_available_mb"] = psutil.virtual_memory().available // (1024 * 1024)
    except ImportError:
        info["psutil"] = "not installed"
    return info


def _generate_crash_report(
    exc_type: type,
    exc_value: BaseException,
    tb,
    app_version: str,
    product: str,
    data_dir: str,
) -> Optional[str]:
    """Generate a detailed JSON crash report under <data_dir>/crashes."""
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "product": product,
        "version": app_version,
        "exception": {
            "type": getattr(exc_type, "__name__", str(exc_type)),
            "message": str(exc_value),
            "traceback": "".join(traceback.format_tb(tb)),
        },
        "system": _get_system_info(),
    }

    crash_dir = os.path.join(data_dir, "crashes")
    os.makedirs(crash_dir, exist_ok=True)
    crash_report_path = os.path.join(crash_dir, f"crash_{int(time.time())}.json")

    try:
        with open(crash_report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return crash_report_path
    except IOError:
        # Fall back to stderr if we cannot write the report
        print(f"[CrashGuard] Failed to write crash report to {crash_report_path}", file=sys.stderr)
        return None


# ---------------------------
# Self-heal
# ---------------------------
def _clear_cache(product: str) -> bool:
    """
    A self-heal recipe that clears the application's temporary cache directory.
    Returns True on success, False on failure.
    """
    logger = logging.getLogger(product)
    cache_dir = os.path.join(_get_data_dir(product), "cache")
    if not os.path.exists(cache_dir):
        logger.info("Self-heal: Cache directory does not exist; skipping clear.")
        return True

    logger.warning("Self-heal: Clearing cache directory at %s", cache_dir)
    try:
        # shutil.rmtree is used to recursively delete the directory
        import shutil
        shutil.rmtree(cache_dir)
        return True
    except OSError as e:
        logger.error("Self-heal: Failed to clear cache directory: %s", e)
        return False


def _attempt_self_heal(product: str) -> None:
    """
    Run a sequence of self-healing recipes after a crash.
    This includes clearing the cache and checking for recurring crashes.
    """
    logger = logging.getLogger(product)
    logger.info("Attempting self-heal...")

    # --- Recipe 1: Clear Cache ---
    _clear_cache(product)

    # --- Recipe 2: Check for Recurring Crashes ---
    # This recipe checks for multiple crashes in a short time and suggests Safe Mode.
    data_dir = _get_data_dir(product)
    crash_history_path = os.path.join(data_dir, "crash_history.json")
    max_crashes = 3
    time_window = 60 * 10  # 10 minutes

    try:
        # Load crash history or initialize if it doesn't exist
        history = []
        if os.path.exists(crash_history_path):
            with open(crash_history_path, "r", encoding="utf-8") as f:
                history = json.load(f)

        # Add the current crash timestamp
        now = int(time.time())
        history.append(now)

        # Keep only crashes within the time window
        recent_crashes = [t for t in history if now - t < time_window]

        # If we have too many recent crashes, trigger the safe mode flag
        if len(recent_crashes) >= max_crashes:
            logger.warning("Recurring crashes detected! Suggesting Safe Mode on next launch.")
            # This flag file will be checked by the application on startup.
            with open(os.path.join(data_dir, "safemode.flag"), "w", encoding="utf-8") as f:
                f.write("1")
            # Reset the history to prevent immediate re-triggering
            recent_crashes = []

        # Save the updated history
        with open(crash_history_path, "w", encoding="utf-8") as f:
            json.dump(recent_crashes, f)

    except (IOError, json.JSONDecodeError) as e:
        logger.error("Could not update crash history: %s", e)

    logger.info("Self-heal attempt finished.")


# ---------------------------
# Public API
# ---------------------------
def install_crash_guard(app_version: str, product: str) -> logging.Logger:
    """
    Initialize logging and install a global crash handler.
    Call once at application startup.

    Returns:
        The configured logger for the product.
    """
    # Paths
    data_dir = _get_data_dir(product)
    log_dir = os.path.join(data_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Logger
    logger = logging.getLogger(product)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        handler = RotatingFileHandler(
            os.path.join(log_dir, "app.log"),
            maxBytes=2_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Crash hook
    def _crash_handler(exc_type, exc_value, tb):
        logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, tb))
        report_path = _generate_crash_report(exc_type, exc_value, tb, app_version, product, data_dir)
        if report_path:
            logger.error("Crash report saved to: %s", report_path)
        _attempt_self_heal(product)
        print(f"\nA critical error occurred in {product}.", file=sys.stderr)
        if report_path:
            print(f"A crash report has been saved to: {report_path}", file=sys.stderr)

    sys.excepthook = _crash_handler

    logger.info("CrashGuard initialized for %s v%s", product, app_version)
    logger.info("User data directory: %s", data_dir)
    return logger


def setup_crash_guard() -> logging.Logger:
    """
    Convenience initializer using default product/version.
    Tests and simple apps can call this without parameters.
    """
    return install_crash_guard(APP_VERSION_DEFAULT, APP_NAME_DEFAULT)
