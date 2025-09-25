import os
import subprocess
import sys

# --- Configuration ---
APP_NAME = "Py2WinPro"
ENTRY_POINT = "src/main.py"
ICON_PATH = "assets/app.ico"  # Placeholder path
DIST_PATH = "dist"
BUILD_PATH = "build"

def run_pyinstaller():
    """Run the PyInstaller command and capture its output."""
    command = [
        sys.executable,
        "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onefile",
        "--windowed",
        f"--icon={ICON_PATH}",
        "--distpath", DIST_PATH,
        "--workpath", BUILD_PATH,
        "--clean",
        ENTRY_POINT,
    ]

    print("Running PyInstaller...")
    print(" ".join(command))

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )

    log_lines = []
    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            print(output.strip())
            log_lines.append(output.strip())

    return process.poll(), log_lines

def analyze_build_logs(logs: list[str]):
    """
    A simple self-debugging feature that analyzes build logs for common issues.
    """
    print("\n--- Build Log Analysis ---")
    issues_found = 0

    # Example check: Look for missing modules
    for line in logs:
        if "ModuleNotFoundError" in line:
            issues_found += 1
            print(f"Potential Issue: Missing module detected -> {line}")

    if issues_found == 0:
        print("No common issues found in the build logs.")
    else:
        print(f"Found {issues_found} potential issue(s).")

def main():
    """Main build script."""
    # Create a dummy icon file if it doesn't exist
    if not os.path.exists(ICON_PATH):
        print(f"Warning: Icon file not found at {ICON_PATH}. Creating a dummy file.")
        os.makedirs(os.path.dirname(ICON_PATH), exist_ok=True)
        with open(ICON_PATH, "w") as f:
            f.write("")

    exit_code, logs = run_pyinstaller()
    analyze_build_logs(logs)

    if exit_code == 0:
        print("\nBuild successful!")
        print(f"Executable created at: {os.path.join(DIST_PATH, APP_NAME + '.exe')}")
    else:
        print(f"\nBuild failed with exit code {exit_code}.")
        sys.exit(exit_code)

if __name__ == "__main__":
    main()