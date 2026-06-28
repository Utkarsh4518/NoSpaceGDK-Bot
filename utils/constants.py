"""Constants used across the NoSpaceFGK bot.

This module houses static, read-only definitions to avoid hardcoding values
across the codebase.
"""

from pathlib import Path
from typing import Final

# Root Directories
ROOT_DIR: Final[Path] = Path(__file__).resolve().parent.parent
LOGS_DIR: Final[Path] = ROOT_DIR / "logs"
DATA_DIR: Final[Path] = ROOT_DIR / "data"
COGS_DIR: Final[Path] = ROOT_DIR / "cogs"

# Bot Details
BOT_NAME: Final[str] = "NoSpaceFGK"
BOT_VERSION: Final[str] = "0.1.0"

# Color Codes for Embeds (Hex Values)
COLOR_SUCCESS: Final[int] = 0x2ECC71  # Emerald Green
COLOR_ERROR: Final[int] = 0xE74C3C    # Alizarin Red
COLOR_WARNING: Final[int] = 0xF1C40F  # Sun Flower Yellow
COLOR_INFO: Final[int] = 0x3498DB     # Peter River Blue
