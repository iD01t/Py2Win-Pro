import sys
import os

class SafeMode:
    """
    A utility class to check if the application should be launched in Safe Mode.

    Safe Mode provides a restricted environment for debugging and recovery.
    It can be triggered by either of the following methods:
    1. A command-line argument: `--safe-mode`
    2. An environment variable: `PY2WINPRO_SAFE_MODE=1`
    """

    _is_enabled = None

    @classmethod
    def enabled(cls) -> bool:
        """
        Checks if Safe Mode is enabled via command-line args or an env var.

        The result is cached after the first check to ensure consistency
        throughout the application's lifecycle.

        Returns:
            True if Safe Mode is enabled, False otherwise.
        """
        if cls._is_enabled is None:
            # 1. Check for the command-line flag
            arg_enabled = "--safe-mode" in sys.argv

            # 2. Check for the environment variable
            env_enabled = os.getenv("PY2WINPRO_SAFE_MODE", "0") == "1"

            cls._is_enabled = arg_enabled or env_enabled

        return cls._is_enabled
