import time
import sys
import logging

# Import the necessary components from our resilience modules
from py2win.crash_guard import setup_crash_guard, APP_NAME
from py2win.preflight import run_preflight_checks
from py2win.debug_daemon import Heartbeat, DebugDaemon

# It's good practice to get the logger by name after it has been configured
logger = logging.getLogger(APP_NAME)

def main():
    """The main entry point for the Py2WinPro application."""
    # 1. Initialize CrashGuard and Logging
    # This MUST be the very first step to ensure all subsequent startup
    # errors are caught and properly logged.
    setup_crash_guard()
    logger.info("========================================")
    logger.info("Application starting up...")
    logger.info("========================================")

    # 2. Run Pre-flight Checks
    logger.info("Running pre-flight checks...")
    all_checks_passed, report = run_preflight_checks()

    if not all_checks_passed:
        logger.error("Critical pre-flight checks failed. Aborting startup.")
        # In a real GUI app, we would show a user-friendly dialog with the report.
        # For a console app, we print the failures to stderr and exit.
        print("Error: Critical pre-flight checks failed. The application cannot start.", file=sys.stderr)
        print("Please review the following errors:", file=sys.stderr)
        for result in report['results']:
            if not result['success'] and result['critical']:
                print(f"  - Check: '{result['check']}' | Message: {result['message']}", file=sys.stderr)
        sys.exit(1)

    logger.info("All pre-flight checks passed successfully.")

    # 3. Set up the Heartbeat probe and the DebugDaemon watchdog
    heartbeat = Heartbeat()
    debug_daemon = DebugDaemon(heartbeat)
    debug_daemon.start()

    # 4. Main Application Loop (Placeholder)
    # This loop simulates a running application by periodically sending a
    # heartbeat signal. In a real app, this would be the GUI event loop
    # or main processing logic.
    logger.info("Main application loop started. Press Ctrl+C to exit.")
    try:
        loop_count = 0
        while True:
            loop_count += 1
            logger.info("Main loop is running (iteration %d)...", loop_count)

            # Signal that the application is alive and responsive.
            heartbeat.beat()

            # Simulate doing work
            time.sleep(5)

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. Shutting down gracefully.")

    finally:
        # 5. Graceful Shutdown Procedure
        logger.info("Initiating shutdown...")
        debug_daemon.stop()
        # Wait for the daemon thread to finish its current cycle
        debug_daemon.join(timeout=3)
        logger.info("========================================")
        logger.info("Application has shut down.")
        logger.info("========================================")

if __name__ == "__main__":
    main()
