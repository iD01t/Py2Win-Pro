import threading
import time
import logging

# Use the same application name as defined in other modules
APP_NAME = "Py2WinPro"
# Get the logger instance configured in crash_guard.py
logger = logging.getLogger(APP_NAME)

# Define the maximum time in seconds before the app is considered stalled
HEARTBEAT_TTL = 10

class Heartbeat:
    """
    A simple class to track the application's liveness. The main application
    should call the beat() method periodically.
    """
    def __init__(self):
        """Initializes the heartbeat with the current time."""
        self.last_beat = time.time()

    def beat(self):
        """Signals that the application is still alive and responsive."""
        self.last_beat = time.time()
        logger.debug("Heartbeat signal received.")

def apply_remediation():
    """
    A placeholder for remediation actions when the app becomes unresponsive.
    This function is called by the DebugDaemon when a heartbeat stalls.
    """
    # In a real-world application, this could trigger actions such as:
    # - Clearing a specific cache that might be causing a deadlock
    # - Restarting a frozen worker thread
    # - Toggling a feature flag to disable a problematic component
    logger.warning("Applying remediation recipe due to stalled heartbeat...")
    # For now, it's a placeholder.
    pass

class DebugDaemon(threading.Thread):
    """
    A watchdog thread that monitors the application's heartbeat.
    If the heartbeat signal is not received within the HEARTBEAT_TTL,
    it triggers a remediation process.
    """
    def __init__(self, heartbeat_probe: Heartbeat):
        """
        Initializes the daemon.

        Args:
            heartbeat_probe: An instance of the Heartbeat class to monitor.
        """
        super().__init__(daemon=True, name="DebugDaemon")
        self.heartbeat_probe = heartbeat_probe
        self.running = True

    def run(self):
        """The main loop for the daemon thread."""
        logger.info("DebugDaemon started. Monitoring application heartbeat (TTL: %d seconds).", HEARTBEAT_TTL)
        while self.running:
            try:
                time_since_last_beat = time.time() - self.heartbeat_probe.last_beat
                if time_since_last_beat > HEARTBEAT_TTL:
                    logger.warning(
                        "Heartbeat stalled for %.2f seconds! Applying remediation.",
                        time_since_last_beat
                    )
                    apply_remediation()
                    # After remediation, we reset the beat to prevent the
                    # daemon from firing continuously for the same stall.
                    self.heartbeat_probe.beat()

            except Exception:
                logger.exception("An error occurred within the DebugDaemon.")

            # The check interval is frequent enough to be responsive but not
            # so frequent that it adds significant overhead.
            time.sleep(2)

    def stop(self):
        """Stops the daemon thread gracefully."""
        logger.info("Stopping DebugDaemon.")
        self.running = False
