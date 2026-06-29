"""Pagination utilities and Views for NoSpaceFGK.

Defines a generic PaginationView base class using standard Discord buttons
(Home, Previous, Next, Close) to navigate a list of embeds.
"""

from typing import List
import discord


class PaginationView(discord.ui.View):
    """A generic, reusable pagination View for embeds."""

    def __init__(self, author_id: int, embeds: List[discord.Embed], timeout: float = 120.0) -> None:
        """Initialize the pagination view.

        Args:
            author_id: The Discord User ID authorized to navigate pages.
            embeds: A list of configured discord.Embed objects to page through.
            timeout: Interaction timeout in seconds.
        """
        super().__init__(timeout=timeout)
        self.author_id: int = author_id
        self.embeds: List[discord.Embed] = embeds
        self.current_page: int = 0
        self.message: discord.InteractionMessage | discord.Message | None = None
        self._update_button_states()

    def _update_button_states(self) -> None:
        """Update button enablement states based on the current page index."""
        total_pages = len(self.embeds)

        # Home button (index 0)
        self.children[0].disabled = (self.current_page == 0) or total_pages <= 1
        # Previous button (index 1)
        self.children[1].disabled = (self.current_page == 0) or total_pages <= 1
        # Next button (index 2)
        self.children[2].disabled = (self.current_page == total_pages - 1) or total_pages <= 1

    async def update_page(self, interaction: discord.Interaction) -> None:
        """Update the interaction response with the current page details.

        Args:
            interaction: The invoking interaction.
        """
        self._update_button_states()
        await interaction.response.edit_message(
            embed=self.embeds[self.current_page],
            view=self
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Verify that the user triggering the interaction is the authorized author.

        Args:
            interaction: The invoking interaction.

        Returns:
            True if authorized, False otherwise.
        """
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "This menu is restricted to the command issuer.",
                ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        """Disable all buttons upon view timeout to prevent dead interactions."""
        if self.message:
            for child in self.children:
                if isinstance(child, discord.ui.Button):
                    child.disabled = True
            try:
                if isinstance(self.message, discord.Interaction):
                    await self.message.edit_original_response(view=self)
                else:
                    await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Home", style=discord.ButtonStyle.secondary, emoji="🏠")
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Navigate to the first page (index 0)."""
        self.current_page = 0
        await self.update_page(interaction)

    @discord.ui.button(label="Prev", style=discord.ButtonStyle.primary, emoji="⬅️")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Navigate to the previous page."""
        if self.current_page > 0:
            self.current_page -= 1
        await self.update_page(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, emoji="➡️")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Navigate to the next page."""
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
        await self.update_page(interaction)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="❌")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """Close the menu and delete the response message."""
        await interaction.response.defer()
        try:
            await interaction.delete_original_response()
        except discord.HTTPException:
            pass
        self.stop()
