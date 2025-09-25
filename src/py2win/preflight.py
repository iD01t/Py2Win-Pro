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
# Check Registry & Runner
# ---------------------------
class CheckRegistry:
    """A registry for pre-flight checks, organized by category."""
    def __init__(self, product_name: str):
        self.product_name = product_name
        self._checks = {
            "core": [
                {"name": "Operating System", "fn": self.check_os, "critical": True},
                {"name": "Python Version", "fn": self.check_python_version, "critical": False},
                {"name": "Virtual Environment", "fn": self.check_virtual_env, "critical": False},
            ],
            "resource": [
                {"name": "Available Disk Space", "fn": self.check_disk_space, "critical": True},
                {"name": "User Data Permissions", "fn": self.check_write_permissions, "critical": True},
            ],
            "dependency": [
                {"name": "Tcl/Tk Presence", "fn": self.check_tcl_tk, "critical": False},
                {"name": "VC++ Redistributable", "fn": self.check_vc_redist, "critical": False},
                {"name": "FFmpeg Presence", "fn": self.check_ffmpeg, "critical": False},
            ],
        }

    def list_checks(self) -> list[dict]:
        """Return a flattened list of all registered checks."""
        return [check for category in self._checks.values() for check in category]

    # --- Check Implementations ---
    def check_os(self) -> tuple[bool, str]:
        os_name = platform.system()
        if os_name not in ["Windows", "Linux"]:
            return False, f"Unsupported OS: '{os_name}'. This application targets Windows."
        return True, f"OS check passed: {os_name} {platform.release()}"

    def check_python_version(self) -> tuple[bool, str]:
        if sys.version_info < MIN_PYTHON_VERSION:
            version_str = ".".join(map(str, sys.version_info[:3]))
            min_version_str = ".".join(map(str, MIN_PYTHON_VERSION))
            return False, f"Python {version_str} too old. Minimum required: {min_version_str}"
        return True, f"Python version check passed: {sys.version.split()[0]}"

    def check_disk_space(self) -> tuple[bool, str]:
        try:
            _, _, free = shutil.disk_usage(os.path.expanduser("~"))
            free_mb = free // (1024 * 1024)
            if free_mb < MIN_DISK_SPACE_MB:
                return False, f"Insufficient disk space. Required: {MIN_DISK_SPACE_MB}MB, Available: {free_mb}MB"
            return True, f"Disk space check passed. Available: {free_mb}MB"
        except FileNotFoundError as e:
            return False, f"Disk space check failed. Could not find path: {e}"

    def check_write_permissions(self) -> tuple[bool, str]:
        path_to_check = _get_data_dir(self.product_name)
        try:
            os.makedirs(path_to_check, exist_ok=True)
            test_file_path = os.path.join(path_to_check, f"permission_test_{os.getpid()}.tmp")
            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write("test")
            os.remove(test_file_path)
            return True, f"Write permissions check passed for: {path_to_check}"
        except (OSError, IOError) as e:
            return False, f"Write permissions check failed for '{path_to_check}': {e}"

    def check_tcl_tk(self) -> tuple[bool, str]:
        try:
            import tkinter
            from tkinter import TclError
        except ImportError:
            return False, "Tcl/Tk check failed: tkinter module could not be imported."
        try:
            root = tkinter.Tk()
            root.destroy()
            return True, "Tcl/Tk check passed."
        except TclError as e:
            return False, f"Tcl/Tk check failed: could not initialize Tkinter. Reason: {e}"

    def check_vc_redist(self) -> tuple[bool, str]:
        if sys.platform != "win32":
            return True, "VC++ Redistributable check skipped (not on Windows)."
        try:
            import winreg
            key_path = r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\X64"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                if winreg.QueryValueEx(key, "Installed")[0] == 1:
                    return True, "VC++ Redistributable (x64) check passed."
        except FileNotFoundError:
            return False, "VC++ Redistributable (x64) not found in registry."
        except OSError:
            return False, "VC++ Redistributable check failed due to a registry access error."
        return False, "VC++ Redistributable (x64) check failed for an unknown reason."

    def check_ffmpeg(self) -> tuple[bool, str]:
        if shutil.which("ffmpeg"):
            return True, "FFmpeg check passed (found in PATH)."
        return False, "FFmpeg check failed (not found in PATH)."

    def check_virtual_env(self) -> tuple[bool, str]:
        if sys.prefix != sys.base_prefix:
            return True, "Virtual environment check passed."
        return False, "Not running in a virtual environment."


def run_preflight(product_name: str) -> bool:
    """
    Run pre-flight checks, log results, write JSON report to the data dir,
    and return True only if all critical checks pass.
    """
    logger = _get_logger(product_name)
    data_dir = _get_data_dir(product_name)
    report_path = os.path.join(data_dir, "PreflightReport.json")
    registry = CheckRegistry(product_name)
    checks_to_run = registry.list_checks()

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
