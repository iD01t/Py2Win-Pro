import sys
import time
import logging

# Import our application modules
from py2win.crash_guard import install_crash_guard
from py2win.debug_daemon import DebugDaemon, Heartbeat
from py2win.preflight import run_preflight
from py2win.safe_mode import SafeMode

# --- Application Constants ---
APP_PRODUCT = "Py2WinPro"
APP_VERSION = "1.0.0"

def app_main():
    """Main application logic loop."""
    logger = logging.getLogger(APP_PRODUCT)
    logger.info("Main application loop starting.")

    # Set up and start the watchdog daemon
    heartbeat = Heartbeat()
    debug_daemon = DebugDaemon(heartbeat_probe=heartbeat)
    debug_daemon.start()

    try:
        while True:
            # Signal that the main loop is alive
            heartbeat.beat()
            logger.info("...application is running...")

            # In a real app, this would be the GUI mainloop or a worker process
            time.sleep(2)

    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Exiting gracefully.")

    finally:
        # Cleanly stop the daemon thread
        if debug_daemon.is_alive():
            debug_daemon.stop()
            debug_daemon.join()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    # This basic config sets up logging to the console.
    # install_crash_guard will add a file handler for persistence.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 1. Install the global exception handler. This must be done first.
    install_crash_guard(app_version=APP_VERSION, product=APP_PRODUCT)

    # 2. Check for Safe Mode.
    if SafeMode.enabled():
        logging.warning("Launching in SAFE MODE. Some features may be disabled.")
        # In a real app, we might skip pre-flight checks or other initializers here.

    # 3. Run pre-flight checks to ensure the environment is sane.
    if not run_preflight(product_name=APP_PRODUCT):
        sys.exit(2) # Exit with a specific code for pre-flight failure.

    # 4. Start the main application.
    app_main()
