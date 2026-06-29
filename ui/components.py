"""Reusable Discord UI components for NoSpaceFGK.

Defines confirmation dialog views and standardized selection components.
"""

from typing import Any
import discord


class ConfirmationView(discord.ui.View):
    """A standard two-button (Confirm/Cancel) confirmation dialog.

    Restricts response interactions to the triggering author.
    """

    def __init__(self, author_id: int, timeout: float = 60.0) -> None:
        """Initialize the confirmation view.

        Args:
            author_id: The Discord User ID authorized to confirm or cancel.
            timeout: Interaction timeout in seconds.
            view_type: Custom typing metadata.
        """
        super().__init__(timeout=timeout)
        self.author_id: int = author_id
        self.value: bool | None = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Handle execution confirmation.

        Args:
            interaction: The invoking Interaction.
            button: The triggered button instance.
        """
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This menu is restricted to the command issuer.", ephemeral=True)
            return

        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Handle execution cancellation.

        Args:
            interaction: The invoking Interaction.
            button: The triggered button instance.
        """
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("This menu is restricted to the command issuer.", ephemeral=True)
            return

        self.value = False
        await interaction.response.defer()
        self.stop()
