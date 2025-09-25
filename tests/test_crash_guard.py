import unittest
import subprocess
import sys
import os
import json
import glob
import shutil

# This is a bit of a hack to import from the src directory.
# A better solution would be to install the package in editable mode.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from py2win.crash_guard import _get_data_dir

class TestCrashGuard(unittest.TestCase):
    """
    Acceptance test for the CrashGuard functionality.
    It runs a crashing script in a subprocess and verifies the output.
    """

    PRODUCT_NAME = "Py2WinPro_Test"

    def setUp(self):
        """Set up the test environment by cleaning old crash reports."""
        self.data_dir = _get_data_dir(self.PRODUCT_NAME)
        self.crashes_dir = os.path.join(self.data_dir, "crashes")
        # Clean up the entire test product directory before the test
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)

    def tearDown(self):
        """Clean up after the test by removing the test product directory."""
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)

    def test_crash_report_generation(self):
        """
        Verify that running a script that crashes results in a JSON crash report
        with the correct information.
        """
        # Path to the helper script that is designed to crash
        crasher_script_path = os.path.join(os.path.dirname(__file__), "helpers", "crasher.py")

        # Run the crasher script as a subprocess
        result = subprocess.run(
            [sys.executable, crasher_script_path],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        # Check that the user-facing message was printed to stderr
        self.assertIn("A critical error occurred", result.stderr)
        self.assertIn("crash report has been saved", result.stderr)

        # Find the generated crash report file. There should be exactly one.
        self.assertTrue(os.path.exists(self.crashes_dir), "Crashes directory was not created.")
        crash_files = glob.glob(os.path.join(self.crashes_dir, "crash_*.json"))
        self.assertEqual(len(crash_files), 1, "Expected exactly one crash report file.")

        report_path = crash_files[0]

        # Verify the content of the crash report
        with open(report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)

        self.assertEqual(report_data.get("product"), self.PRODUCT_NAME)
        self.assertEqual(report_data.get("version"), "0.0.1-test")
        self.assertEqual(report_data.get("exception", {}).get("type"), "ValueError")
        self.assertEqual(report_data.get("exception", {}).get("message"), "This is a deliberate crash for testing purposes.")
        self.assertIn("crasher.py", report_data.get("exception", {}).get("traceback", ""))

if __name__ == '__main__':
    unittest.main(verbosity=2)
