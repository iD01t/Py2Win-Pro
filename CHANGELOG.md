# Py2Win Pro - Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure with `src`, `tests`, `docs`, and `assets` directories.
- Core resilience framework:
    - **CrashGuard:** Global exception handling and JSON crash reporting.
    - **Logging:** Structured, rotating file-based logging system.
    - **DebugDaemon:** Watchdog thread for monitoring application responsiveness via a heartbeat mechanism.
    - **Pre-flight Checks:** Environment validation for OS, Python version, disk space, and permissions.
- Main application entry point (`src/main.py`) that integrates all core components.
- Initial project documentation (`README.md`, `CHANGELOG.md`, `LICENSE.txt`).

---
*© 2025 iD01t Productions, Guillaume Lessard. All rights reserved.*
