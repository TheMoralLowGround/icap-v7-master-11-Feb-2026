"""
Configuration utilities for classification processing.
"""
import os


def is_sync_mode() -> bool:
    """
    Check if SYNC_MODE is enabled from environment variable.

    Returns:
        True if sync mode is enabled, False otherwise (default: async mode)

    Environment variable SYNC_MODE:
        - Not set: async mode (default)
        - "True"/"1"/"yes": sync mode
        - "False"/"0"/"no": async mode
    """
    sync_mode = os.getenv("SYNC_MODE", "False")
    return sync_mode.lower() in ("true", "1", "yes")

def is_majority_voting() -> bool:
    "Check if MAJORITY_VOTING is enabled from environment variable."
    majority_voting = os.getenv("MAJORITY_VOTING", "False")
    return majority_voting.lower() in ("true", "1", "yes")