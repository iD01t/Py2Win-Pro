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

This project is in the initial development phase. The core resilience features have been implemented as a foundation.

## 🛠️ How to Run

1.  Ensure you have Python 3.8+ installed.
2.  Run the main entry point from the root directory:
    ```bash
    python3 src/main.py
    ```
    *Note: The application is currently designed to run on Windows only. The pre-flight check will prevent it from starting on other operating systems.*

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
