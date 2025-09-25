import unittest
import os
import shutil
import json
import time
import sys
from unittest.mock import patch, MagicMock

# Add src to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from py2win.crash_guard import _clear_cache, _attempt_self_heal, _get_data_dir

class TestSelfHeal(unittest.TestCase):
    """Tests for the self-healing functionality."""

    PRODUCT_NAME = "Py2WinPro_SelfHealTest"

    def setUp(self):
        self.data_dir = _get_data_dir(self.PRODUCT_NAME)
        self.cache_dir = os.path.join(self.data_dir, "cache")
        # Clean up before each test
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)
        os.makedirs(self.cache_dir, exist_ok=True)

    def tearDown(self):
        # Clean up after each test
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)

    def test_clear_cache(self):
        """Test that the cache clearing function removes the cache directory."""
        # Create a dummy file in the cache
        with open(os.path.join(self.cache_dir, "test.txt"), "w") as f:
            f.write("test")

        self.assertTrue(os.path.exists(self.cache_dir))
        _clear_cache(self.PRODUCT_NAME)
        self.assertFalse(os.path.exists(self.cache_dir))

    @patch("logging.getLogger")
    def test_recurring_crash_detection(self, mock_getLogger):
        """Test that recurring crashes trigger the safemode flag."""
        # Simulate three crashes
        _attempt_self_heal(self.PRODUCT_NAME)
        time.sleep(1)
        _attempt_self_heal(self.PRODUCT_NAME)
        time.sleep(1)
        _attempt_self_heal(self.PRODUCT_NAME)

        # Check that the safemode flag was created
        safemode_flag_path = os.path.join(self.data_dir, "safemode.flag")
        self.assertTrue(os.path.exists(safemode_flag_path))

if __name__ == "__main__":
    unittest.main()