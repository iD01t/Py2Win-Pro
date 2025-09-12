import unittest
import sys
import os

# Add the 'src' directory to the Python path to allow for package imports
# This allows us to run tests from the root directory and have imports work correctly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

class TestSanity(unittest.TestCase):
    """
    A simple sanity check test suite to ensure that all primary modules
    are importable and expose their key functions and classes.
    """

    def test_crash_guard_module_import(self):
        """
        Verify that the crash_guard module can be imported and contains the
        `setup_crash_guard` function.
        """
        try:
            from py2win import crash_guard
            self.assertTrue(callable(crash_guard.setup_crash_guard), "setup_crash_guard should be a callable function")
        except ImportError as e:
            self.fail(f"Failed to import py2win.crash_guard: {e}")

    def test_debug_daemon_module_import(self):
        """
        Verify that the debug_daemon module can be imported and contains the
        `DebugDaemon` and `Heartbeat` classes.
        """
        try:
            from py2win import debug_daemon
            self.assertTrue(hasattr(debug_daemon, 'DebugDaemon'), "Module should have DebugDaemon class")
            self.assertTrue(hasattr(debug_daemon, 'Heartbeat'), "Module should have Heartbeat class")
        except ImportError as e:
            self.fail(f"Failed to import py2win.debug_daemon: {e}")

    def test_preflight_module_import(self):
        """
        Verify that the preflight module can be imported and contains the
        `run_preflight_checks` function.
        """
        try:
            from py2win import preflight
            self.assertTrue(callable(preflight.run_preflight_checks), "run_preflight_checks should be a callable function")
        except ImportError as e:
            self.fail(f"Failed to import py2win.preflight: {e}")

    def test_main_module_import(self):
        """
        Verify that the main entry point module can be imported and exposes
        the `main` function.
        """
        try:
            import main
            self.assertTrue(callable(main.main), "main module should have a callable main function")
        except ImportError as e:
            self.fail(f"Failed to import main: {e}")

if __name__ == '__main__':
    unittest.main()
