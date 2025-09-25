# Py2Win Pro

**© Guillaume Lessard – iD01t Productions. All Rights Reserved. Licensed under iD01t Productions License.**

---

## 🚀 Overview

Py2Win Pro is a professional tool designed to create robust, production-ready Windows applications from Python scripts. It automates the process of packaging, hardening, and deploying applications, incorporating enterprise-grade features for reliability and supportability.

This project is being built with a "bullet-proof" philosophy, including:
-   **CrashGuard:** Catches unhandled exceptions and generates detailed crash reports.
-   **DebugDaemon:** A watchdog that monitors application health and can perform self-healing actions.
-   **Pre-flight Checks:** Verifies the environment before launch to prevent common errors.
-   **Structured Logging:** Provides detailed, structured logs for easy debugging.

## 📋 Current Status

This project is fully functional and includes a comprehensive suite of resilience features, a graphical user interface, and a build system for creating a standalone executable.

## ✨ Features

-   **CrashGuard:** Catches unhandled exceptions, generates detailed crash reports with system information, and attempts self-healing actions.
-   **Self-Healing:** Automatically clears the cache on startup and detects recurring crashes to suggest launching in Safe Mode.
-   **DebugDaemon:** A watchdog that monitors application health and can perform self-healing actions.
-   **Pre-flight Checks:** Verifies the environment (OS, Python version, disk space, dependencies) before launch to prevent common errors.
-   **GUI Control Panel:** A Tkinter-based UI for monitoring logs, testing crash recovery, and managing the application.
-   **One-Click Build:** A PyInstaller-based build script to create a single, self-contained executable.

## 🛠️ How to Run

### From Source

1.  Ensure you have Python 3.8+ installed.
2.  It is recommended to create a virtual environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```
3.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Run the main entry point from the root directory:
    ```bash
    python3 src/main.py
    ```

### Building the Executable

1.  Follow the steps above to set up the environment and install dependencies.
2.  Run the build script:
    ```bash
    python3 build.py
    ```
3.  The executable will be located in the `dist` directory.

## 📂 Project Structure

```
/src            → Main source code for the application
  /py2win       → Core Python package
    /crash_guard.py
    /debug_daemon.py
    /preflight.py
  /main.py      → Main application entry point
/docs           → Documentation files
/assets         → Application assets (icons, images)
/tests          → Test suite
README.md       → This file
CHANGELOG.md    → Record of changes
LICENSE.txt     → License file
```
