import sys
import os

# Add the 'src' directory to the Python path to allow for package imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from py2win.crash_guard import install_crash_guard

def main():
    """
    A simple script that installs the crash guard and then deliberately crashes.
    This is used by the acceptance test to verify crash report generation.
    """
    # Use a unique product name for this test to avoid interfering with
    # the actual application's logs or crash reports.
    APP_PRODUCT = "Py2WinPro_Test"
    APP_VERSION = "0.0.1-test"

    # Install the crash handler
    install_crash_guard(app_version=APP_VERSION, product=APP_PRODUCT)

    # This exception should be caught by our custom sys.excepthook
    raise ValueError("This is a deliberate crash for testing purposes.")

if __name__ == "__main__":
    main()
