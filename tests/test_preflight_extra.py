import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add src to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from py2win.preflight import CheckRegistry

class TestPreflightExtra(unittest.TestCase):
    """Tests for the expanded and refactored pre-flight checks."""

    def setUp(self):
        self.registry = CheckRegistry("TestApp")

    def test_check_virtual_env(self):
        """Test the virtual environment check."""
        with patch("sys.prefix", "/usr/bin"):
            with patch("sys.base_prefix", "/usr"):
                # sys.prefix != sys.base_prefix means we are in a venv
                ok, msg = self.registry.check_virtual_env()
                self.assertTrue(ok)
                self.assertIn("passed", msg)

            with patch("sys.base_prefix", "/usr/bin"):
                # sys.prefix == sys.base_prefix means we are not in a venv
                ok, msg = self.registry.check_virtual_env()
                self.assertFalse(ok)
                self.assertIn("Not running", msg)

    @patch("tkinter.Tk")
    def test_check_tcl_tk_success(self, mock_tk):
        """Test the Tcl/Tk check (success case)."""
        ok, msg = self.registry.check_tcl_tk()
        self.assertTrue(ok)
        self.assertIn("passed", msg)
        mock_tk.assert_called_once()

    @patch("builtins.__import__", side_effect=ImportError)
    def test_check_tcl_tk_import_error(self, mock_import):
        """Test the Tcl/Tk check (ImportError case)."""
        ok, msg = self.registry.check_tcl_tk()
        self.assertFalse(ok)
        self.assertIn("could not be imported", msg)

    @patch("shutil.which", return_value="/usr/bin/ffmpeg")
    def test_check_ffmpeg_found(self, mock_which):
        """Test the FFmpeg check (found case)."""
        ok, msg = self.registry.check_ffmpeg()
        self.assertTrue(ok)
        self.assertIn("found in PATH", msg)

    @patch("shutil.which", return_value=None)
    def test_check_ffmpeg_not_found(self, mock_which):
        """Test the FFmpeg check (not found case)."""
        ok, msg = self.registry.check_ffmpeg()
        self.assertFalse(ok)
        self.assertIn("not found in PATH", msg)

if __name__ == "__main__":
    unittest.main()