# preflight.py
import sys
import os
import shutil
import platform
import json
import time
import logging

# --- App constants ---
APP_NAME = "Py2WinPro"
MIN_PYTHON_VERSION = (3, 8)
MIN_DISK_SPACE_MB = 100  # minimum free space required in MB


# ---------------------------
# Utilities
# ---------------------------
def _get_data_dir(product_name: str) -> str:
    """Return the per-user data directory for the product."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return os.path.join(base, product_name)
    # Other OSes (used for CI/sandbox only)
    return os.path.join(os.path.expanduser("~"), f".{product_name.lower()}")


def _get_logger(product_name: str) -> logging.Logger:
    """Configure and return a basic logger writing to the product data dir."""
    data_dir = _get_data_dir(product_name)
    log_dir = os.path.join(data_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(product_name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(os.path.join(log_dir, "preflight.log"), encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger


# ---------------------------
# Individual checks
# ---------------------------
def check_os() -> tuple[bool, str]:
    """Verify supported OS (Windows primary, Linux allowed for sandbox/CI)."""
    os_name = platform.system()
    if os_name not in ["Windows", "Linux"]:
        return False, f"Unsupported OS: '{os_name}'. This application targets Windows."
    return True, f"OS check passed: {os_name} {platform.release()}"


def check_python_version() -> tuple[bool, str]:
    """Verify the Python interpreter version (less critical when bundled)."""
    if sys.version_info < MIN_PYTHON_VERSION:
        version_str = ".".join(map(str, sys.version_info[:3]))
        min_version_str = ".".join(map(str, MIN_PYTHON_VERSION))
        return False, f"Python {version_str} too old. Minimum required: {min_version_str}"
    return True, f"Python version check passed: {sys.version.split()[0]}"


def check_disk_space() -> tuple[bool, str]:
    """Verify there is sufficient free disk space in the user's home directory (MB)."""
    try:
        _, _, free = shutil.disk_usage(os.path.expanduser("~"))
        free_mb = free // (1024 * 1024)
        if free_mb < MIN_DISK_SPACE_MB:
            return False, f"Insufficient disk space. Required: {MIN_DISK_SPACE_MB}MB, Available: {free_mb}MB"
        return True, f"Disk space check passed. Available: {free_mb}MB"
    except FileNotFoundError as e:
        return False, f"Disk space check failed. Could not find path: {e}"


def check_write_permissions(product_name: str) -> tuple[bool, str]:
    """Verify write permissions to the application's data directory."""
    path_to_check = _get_data_dir(product_name)
    try:
        os.makedirs(path_to_check, exist_ok=True)
        test_file_path = os.path.join(path_to_check, f"permission_test_{os.getpid()}.tmp")
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("test")
        os.remove(test_file_path)
        return True, f"Write permissions check passed for: {path_to_check}"
    except (OSError, IOError) as e:
        return False, f"Write permissions check failed for '{path_to_check}': {e}"


def check_tcl_tk() -> tuple[bool, str]:
    """Placeholder for Tcl/Tk presence check."""
    # TODO: Implement a real check for tcl/tk folder and a minimal smoke test.
    return True, "Tcl/Tk check skipped (TODO)."


def check_vc_redist() -> tuple[bool, str]:
    """Placeholder for VC++ Redistributable presence check."""
    # TODO: Implement a real check via registry or bundled installer presence.
    return True, "VC++ Redistributable check skipped (TODO)."


def check_ffmpeg() -> tuple[bool, str]:
    """Placeholder for ffmpeg.exe presence check."""
    # TODO: Implement a real PATH/bundled lookup and version probe.
    return True, "FFmpeg check skipped (TODO)."


# ---------------------------
# Orchestration
# ---------------------------
def run_preflight(product_name: str) -> bool:
    """
    Run pre-flight checks, log results, write JSON report to the data dir,
    and return True only if all critical checks pass.
    """
    logger = _get_logger(product_name)
    data_dir = _get_data_dir(product_name)
    report_path = os.path.join(data_dir, "PreflightReport.json")

    checks_to_run: list[dict] = [
        {"name": "Operating System", "fn": check_os, "critical": True},
        {"name": "Python Version", "fn": check_python_version, "critical": False},
        {"name": "Available Disk Space", "fn": check_disk_space, "critical": True},
        {"name": "User Data Permissions", "fn": lambda: check_write_permissions(product_name), "critical": True},
        {"name": "Tcl/Tk Presence", "fn": check_tcl_tk, "critical": False},
        {"name": "VC++ Redistributable", "fn": check_vc_redist, "critical": False},
        {"name": "FFmpeg Presence", "fn": check_ffmpeg, "critical": False},
    ]

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "product": product_name,
        "overall_status": "PASS",
        "results": [],
    }

    logger.info("--- Starting Pre-flight Checks ---")
    all_critical_passed = True

    for check in checks_to_run:
        ok, msg = check["fn"]()
        logger.info("Check %-22s => %s : %s", check["name"], "PASS" if ok else "FAIL", msg)
        report["results"].append(
            {"check": check["name"], "success": ok, "message": msg, "critical": check["critical"]}
        )
        if not ok and check["critical"]:
            all_critical_passed = False
            report["overall_status"] = "FAIL"

    logger.info("--- Pre-flight Checks Finished --- [ %s ]", report["overall_status"])

    # Write the JSON report
    try:
        os.makedirs(data_dir, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info("Pre-flight report saved to %s", report_path)
    except IOError as e:
        logger.error("FATAL: Could not write pre-flight report to %s: %s", report_path, e)
        all_critical_passed = False

    if not all_critical_passed:
        print("\nError: Critical pre-flight checks failed. The application cannot start.", file=sys.stderr)
        print("See PreflightReport.json for details.", file=sys.stderr)

    return all_critical_passed


def run_preflight_checks() -> tuple[bool, dict]:
    """
    Convenience wrapper for default APP_NAME used by tests or CLI.
    Returns (all_critical_passed, report_dict).
    """
    product = APP_NAME
    data_dir = _get_data_dir(product)
    report_path = os.path.join(data_dir, "PreflightReport.json")

    ok = run_preflight(product)
    # Load the report we just wrote for the caller’s convenience
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception:
        report = {"product": product, "overall_status": "FAIL", "results": []}
    return ok, report
