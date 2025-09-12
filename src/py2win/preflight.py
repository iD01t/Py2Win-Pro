import sys
import os
import shutil
import platform
import json
import time

# Define the application name and log directory consistently
APP_NAME = "Py2WinPro"
LOG_DIR = os.path.join(os.path.expanduser("~"), f".{APP_NAME.lower()}", "logs")
PREFLIGHT_REPORT_PATH = os.path.join(LOG_DIR, "PreflightReport.json")

# --- Pre-flight Requirements ---
MIN_PYTHON_VERSION = (3, 8)
MIN_DISK_SPACE_MB = 100  # Require 100MB of free space

def check_os():
    """Verifies the application is running on a supported OS (Windows)."""
    if platform.system() != "Windows":
        return False, f"Unsupported OS: '{platform.system()}'. This application is designed for Windows."
    return True, f"OS check passed: {platform.system()} {platform.release()}"

def check_python_version():
    """Verifies the Python interpreter version meets the minimum requirement."""
    if sys.version_info < MIN_PYTHON_VERSION:
        version_str = '.'.join(map(str, sys.version_info[:3]))
        min_version_str = '.'.join(map(str, MIN_PYTHON_VERSION))
        return False, f"Python version {version_str} is too old. Minimum required: {min_version_str}"
    return True, f"Python version check passed: {sys.version.split()[0]}"

def check_disk_space():
    """Verifies there is sufficient free disk space in the user's home directory."""
    try:
        _, _, free = shutil.disk_usage(os.path.expanduser("~"))
        free_mb = free // (1024 * 1024)
        if free_mb < MIN_DISK_SPACE_MB:
            return False, f"Insufficient disk space. Required: {MIN_DISK_SPACE_MB}MB, Available: {free_mb}MB"
        return True, f"Disk space check passed. Available space: {free_mb}MB"
    except FileNotFoundError as e:
        return False, f"Disk space check failed. Could not find path: {e}"


def check_write_permissions():
    """Verifies the application has write permissions in its log directory."""
    try:
        # The directory should already exist from logger setup, but we ensure it.
        os.makedirs(LOG_DIR, exist_ok=True)
        # Attempt to create and delete a temporary file
        test_file_path = os.path.join(LOG_DIR, f"permission_test_{os.getpid()}.tmp")
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("test")
        os.remove(test_file_path)
        return True, f"Write permissions check passed for directory: {LOG_DIR}"
    except (OSError, IOError) as e:
        return False, f"Write permissions check failed for '{LOG_DIR}': {e}"

def run_preflight_checks():
    """
    Runs all pre-flight checks, generates a JSON report, and returns the outcome.

    Returns:
        A tuple (bool, dict):
        - True if all critical checks passed, False otherwise.
        - A dictionary containing the detailed report of all checks.
    """
    # List of checks to run. More can be added here easily.
    checks_to_run = [
        {"name": "Operating System", "function": check_os, "critical": True},
        {"name": "Python Version", "function": check_python_version, "critical": True},
        {"name": "Available Disk Space", "function": check_disk_space, "critical": True},
        {"name": "Log Directory Permissions", "function": check_write_permissions, "critical": True},
    ]

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "overall_status": "PASS",
        "results": []
    }
    all_critical_passed = True

    for check in checks_to_run:
        success, message = check["function"]()
        report["results"].append({
            "check": check["name"],
            "success": success,
            "message": message,
            "critical": check["critical"],
        })
        if not success and check["critical"]:
            all_critical_passed = False
            report["overall_status"] = "FAIL"

    # Save the report to a file
    try:
        # Ensure the log directory exists before writing the report
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(PREFLIGHT_REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    except IOError as e:
        # This is a critical failure, as we can't even write the report.
        # It should have been caught by the permissions check.
        print(f"FATAL: Could not write pre-flight report to {PREFLIGHT_REPORT_PATH}: {e}", file=sys.stderr)
        # We should probably exit here in a real app, but for now, we return the failure.
        all_critical_passed = False

    return all_critical_passed, report
