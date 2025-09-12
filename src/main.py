# main.py
import sys
import time
import logging

# Resilience stack
from py2win.crash_guard import install_crash_guard
from py2win.debug_daemon import DebugDaemon, Heartbeat
from py2win.preflight import run_preflight

# SafeMode is optional; fall back to disabled if the module isn’t present yet.
try:
    from py2win.safe_mode import SafeMode  # type: ignore
except Exception:
    class SafeMode:  # minimal shim
        @staticmethod
        def enabled() -> bool:
            return False


# --- Application Constants ---
APP_PRODUCT = "Py2WinPro"
APP_VERSION = "1.0.0"


def app_main() -> None:
    """Main application logic loop (placeholder for GUI/event loop)."""
    logger = logging.getLogger(APP_PRODUCT)
    logger.info("Main application loop starting.")

    # Watchdog and heartbeat
    heartbeat = Heartbeat()
    debug_daemon = DebugDaemon(heartbeat_probe=heartbeat)
    debug_daemon.start()

    try:
        loop_count = 0
        while True:
            loop_count += 1
            heartbeat.beat()  # signal liveness
            logger.info("Application running (iteration %d)…", loop_count)
            # Replace sleep with your GUI mainloop() or work cycle
            time.sleep(2)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Exiting gracefully.")
    finally:
        if debug_daemon.is_alive():
            debug_daemon.stop()
            debug_daemon.join(timeout=3)
        logger.info("Shutdown complete.")


def main() -> None:
    """
    Program entry point:
    1) initialize CrashGuard,
    2) honor Safe Mode,
    3) run pre-flight checks,
    4) start app loop.
    """
    # Console logger (CrashGuard adds file handler)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 1) Global exception handler and file logging
    install_crash_guard(app_version=APP_VERSION, product=APP_PRODUCT)

    # 2) Safe Mode (optional)
    if SafeMode.enabled():
        logging.getLogger(APP_PRODUCT).warning(
            "Launching in SAFE MODE. Some features may be disabled."
        )

    # 3) Pre-flight environment validation
    if not run_preflight(product_name=APP_PRODUCT):
        # Specific code for pre-flight failure so CI/scripts can detect it
        sys.exit(2)

    # 4) Start main application
    app_main()


if __name__ == "__main__":
    main()
