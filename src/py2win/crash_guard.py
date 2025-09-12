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
        "exc_type": getattr(exc_type, "__name__", str(exc_type)),
        "message": str(exc_value),
        "traceback": "".join(traceback.format_tb(tb)),
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
    except IOError:
        # Fall back to stderr if we cannot write the report
        print(f"[CrashGuard] Failed to write crash report to {crash_report_path}", file=sys.stderr)
        return None


# ---------------------------
# Self-heal (placeholder)
# ---------------------------
def _attempt_self_heal(product: str) -> None:
    """
    Placeholder for self-healing logic.
    Examples: disable extensions, clear caches, restart workers, toggle Safe Mode.
    """
    logger = logging.getLogger(product)
    try:
        logger.info("Attempting self-heal… (placeholder)")
        # TODO: implement real remediation recipes
    except Exception as e:
        logger.exception("Self-heal attempt failed: %s", e)


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
