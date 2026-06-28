"""Events package for NoSpaceFGK.

Exposes a dynamic load routine to register modular event cogs automatically.
"""

import importlib
import inspect
from pathlib import Path
from discord.ext import commands
from utils.logger import logger


async def setup(bot: commands.Bot) -> None:
    """Dynamically discover and register all event Cog classes in this package.

    Args:
        bot: The target Bot instance.
    """
    events_dir = Path(__file__).parent

    for filepath in events_dir.glob("*.py"):
        if filepath.name == "__init__.py":
            continue

        module_name = f"events.{filepath.stem}"
        try:
            module = importlib.import_module(module_name)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, commands.Cog) and obj is not commands.Cog:
                    await bot.add_cog(obj(bot))
                    logger.info(f"Loaded event cog: {obj.__name__} from {module_name}")
        except Exception as e:
            logger.error(f"Failed to load event module {module_name}: {e}", exc_info=True)
