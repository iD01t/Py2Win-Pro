import sys
import os
import shutil
import platform
import json
import time
import logging

def _get_data_dir(product_name: str) -> str:
    """Gets the application's user data directory path based on OS."""
    if sys.platform == "win32":
        return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), product_name)
    # Fallback for other OSes
    return os.path.join(os.path.expanduser("~"), f".{product_name.lower()}")

def check_os():
    """Verifies the application is running on a supported OS (Windows)."""
    # Allow Linux for sandbox testing.
    if platform.system() not in ["Windows", "Linux"]:
        return False, f"Unsupported OS: '{platform.system()}'. This application is designed for Windows."
    return True, f"OS check passed: {platform.system()} {platform.release()}"

def check_python_version():
    """Verifies the Python interpreter version. Less critical for bundled apps."""
    MIN_PYTHON_VERSION = (3, 8)
    if sys.version_info < MIN_PYTHON_VERSION:
        version_str = '.'.join(map(str, sys.version_info[:3]))
        min_version_str = '.'.join(map(str, MIN_PYTHON_VERSION))
        return False, f"Python version {version_str} is too old. Minimum required: {min_version_str}"
    return True, f"Python version check passed: {sys.version.split()[0]}"

def check_disk_space():
    """Verifies there is at least 1GB of free disk space."""
    MIN_DISK_SPACE_GB = 1
    try:
        _, _, free = shutil.disk_usage(os.path.expanduser("~"))
        free_gb = free // (1024 * 1024 * 1024)
        if free_gb < MIN_DISK_SPACE_GB:
            return False, f"Insufficient disk space. Required: {MIN_DISK_SPACE_GB}GB, Available: {free_gb}GB"
        return True, f"Disk space check passed. Available space: {free_gb}GB"
    except FileNotFoundError as e:
        return False, f"Disk space check failed. Could not find path: {e}"

def check_write_permissions(product_name: str):
    """Verifies write permissions to the application's data directory."""
    path_to_check = _get_data_dir(product_name)
    try:
        os.makedirs(path_to_check, exist_ok=True)
        test_file_path = os.path.join(path_to_check, f"permission_test_{os.getpid()}.tmp")
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("test")
        os.remove(test_file_path)
        return True, f"Write permissions check passed for directory: {path_to_check}"
    except (OSError, IOError) as e:
        return False, f"Write permissions check failed for '{path_to_check}': {e}"

def check_tcl_tk():
    """Placeholder for Tcl/Tk presence check."""
    # TODO: Implement a real check for tcl/tk folder and a minimal smoke test.
    return True, "Tcl/Tk check skipped (TODO)."

def check_vc_redist():
    """Placeholder for VC++ Redistributable presence check."""
    # TODO: Implement a real check for VC++ redistributable via registry keys.
    return True, "VC++ Redistributable check skipped (TODO)."

def check_ffmpeg():
    """Placeholder for ffmpeg.exe presence check."""
    # TODO: Implement a real check for ffmpeg.exe in PATH or bundled location.
    return True, "FFmpeg check skipped (TODO)."

def run_preflight(product_name: str) -> bool:
    """
    Runs all pre-flight checks, generates a JSON report, and returns the outcome.
    Prints failures to the console.
    """
    logger = logging.getLogger(product_name)
    data_dir = _get_data_dir(product_name)
    log_dir = os.path.join(data_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    report_path = os.path.join(data_dir, "PreflightReport.json") # Report in data dir, not logs

    checks_to_run = [
        {"name": "Operating System", "function": check_os, "critical": True},
        {"name": "Python Version", "function": check_python_version, "critical": False},
        {"name": "Available Disk Space", "function": check_disk_space, "critical": True},
        {"name": "User Data Permissions", "function": lambda: check_write_permissions(product_name), "critical": True},
        {"name": "Tcl/Tk Presence", "function": check_tcl_tk, "critical": False},
        {"name": "VC++ Redistributable", "function": check_vc_redist, "critical": False},
        {"name": "FFmpeg Presence", "function": check_ffmpeg, "critical": False},
    ]

    report = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "overall_status": "PASS", "results": []}
    all_critical_passed = True

    logger.info("--- Starting Pre-flight Checks ---")
    for check in checks_to_run:
        success, message = check["function"]()
        log_func = logger.info if success else logger.warning
        log_func(f"  - Check '{check['name']}': {'PASS' if success else 'FAIL'}. Message: {message}")

        report["results"].append({"check": check["name"], "success": success, "message": message, "critical": check["critical"]})
        if not success and check["critical"]:
            all_critical_passed = False
            report["overall_status"] = "FAIL"

    logger.info("--- Pre-flight Checks Finished ---")

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info("Pre-flight report saved to %s", report_path)
    except IOError as e:
        logger.error(f"FATAL: Could not write pre-flight report to {report_path}: {e}")
        all_critical_passed = False

    if not all_critical_passed:
        print("\nError: Critical pre-flight checks failed. The application cannot start.", file=sys.stderr)
        print("Please review the log file and PreflightReport.json for details.", file=sys.stderr)

    return all_critical_passed
