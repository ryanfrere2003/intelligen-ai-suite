""" has configuration data for the application including commonly used paths"""

from pathlib import Path

#--------------
# PATHS
#--------------

APP_PATH = Path(__file__).resolve().parent
MAILBOX_PATH = APP_PATH / "raw.mbox"
