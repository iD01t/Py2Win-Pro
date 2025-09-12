import unittest
import time
import logging
import sys
import os
from queue import Queue
from logging.handlers import QueueHandler

# Add src to the Python path to allow importing our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from py2win.debug_daemon import DebugDaemon, Heartbeat, HEARTBEAT_TTL

# Use a unique name for the test logger to avoid conflicts
TEST_LOGGER_NAME = "Py2WinPro_DaemonTest"

class TestDebugDaemon(unittest.TestCase):
    """
    Acceptance test for the DebugDaemon's stall detection functionality.
    """

    def setUp(self):
        """
        Set up a logger with a QueueHandler to capture log records from the
        daemon thread in a thread-safe manner.
        """
        self.log_queue = Queue()
        self.logger = logging.getLogger(TEST_LOGGER_NAME)
        self.logger.setLevel(logging.INFO)

        # Ensure a clean slate for handlers
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        self.queue_handler = QueueHandler(self.log_queue)
        self.logger.addHandler(self.queue_handler)

    def tearDown(self):
        """Clean up by removing the test handler."""
        self.logger.removeHandler(self.queue_handler)

    def get_all_log_messages(self) -> list[str]:
        """Retrieve all formatted messages from the log queue."""
        messages = []
        while not self.log_queue.empty():
            messages.append(self.log_queue.get().getMessage())
        return messages

    def test_daemon_detects_stalled_heartbeat(self):
        """
        Verify that the DebugDaemon detects a missed heartbeat and logs a
        remediation attempt.
        """
        # The daemon checks every 2s and stalls after 10s.
        # Waiting for TTL + 1s should be enough to trigger the check.
        STALL_WAIT_TIME = HEARTBEAT_TTL + 1

        heartbeat = Heartbeat()

        # Temporarily replace the logger in the debug_daemon module with our test logger.
        # This allows us to capture the logs from the daemon thread.
        import py2win.debug_daemon
        original_logger = py2win.debug_daemon.logger
        py2win.debug_daemon.logger = self.logger

        daemon = DebugDaemon(heartbeat_probe=heartbeat)
        daemon.start()

        # Let the daemon run and then stop sending heartbeats, simulating a stall.
        time.sleep(STALL_WAIT_TIME)

        daemon.stop()
        daemon.join(timeout=5)

        # Restore the original logger to avoid side effects in other tests.
        py2win.debug_daemon.logger = original_logger

        # Check the captured logs for the expected messages.
        log_messages = self.get_all_log_messages()

        stall_detected = any("Heartbeat stalled" in msg for msg in log_messages)
        remediation_applied = any("Applying remediation recipe" in msg for msg in log_messages)

        self.assertTrue(stall_detected, f"DebugDaemon did not log a stalled heartbeat. Captured logs: {log_messages}")
        self.assertTrue(remediation_applied, f"DebugDaemon did not log a remediation attempt. Captured logs: {log_messages}")

if __name__ == '__main__':
    unittest.main(verbosity=2)
