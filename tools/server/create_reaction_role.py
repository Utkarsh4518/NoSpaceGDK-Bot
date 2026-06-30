"""Create Reaction Role Tool for AI Agent."""

from typing import Any, Dict, Optional
import discord
from services.ai.agent.base_tool import BaseTool
from services.server.reaction_role_service import ReactionRoleService

class CreateReactionRoleTool(BaseTool):
    """Tool for creating a reaction role message setup."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.rr_service: ReactionRoleService = service_container.get(ReactionRoleService)

    @property
    def name(self) -> str:
        return "create_reaction_role"

    @property
    def description(self) -> str:
        return (
            "Create a reaction role setup configuration. Use this when the user asks to create, configure, "
            "or setup a reaction role, button role, or select menu role."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "The Snowflake ID of the channel where the reaction role message should reside."
                },
                "title": {
                    "type": "string",
                    "description": "The title of the reaction role panel."
                },
                "description": {
                    "type": "string",
                    "description": "The description/body text of the reaction role panel."
                },
                "group_name": {
                    "type": "string",
                    "description": "A unique group name for this reaction role configuration."
                },
                "type": {
                    "type": "string",
                    "enum": ["button", "select", "reaction"],
                    "description": "The interaction format: 'button', 'select', or 'reaction' (default emoji)."
                },
                "emoji": {
                    "type": "string",
                    "description": "The emoji (unicode or custom tag) mapped to the role."
                },
                "role_id": {
                    "type": "integer",
                    "description": "The Snowflake ID of the role to assign."
                }
            },
            "required": ["channel_id", "title", "description", "group_name", "type", "emoji", "role_id"]
        }

    @property
    def required_permissions(self) -> list:
        return ["manage_roles"]

    async def execute(self, **kwargs) -> Any:
        channel_id = kwargs["channel_id"]
        title = kwargs["title"]
        description = kwargs["description"]
        group_name = kwargs["group_name"]
        type_ = kwargs["type"]
        emoji = kwargs["emoji"]
        role_id = kwargs["role_id"]
        channel = kwargs["channel"]

        guild = getattr(channel, "guild", None)
        if not guild:
            return {"status": "error", "message": "This command can only be executed within a server."}

        target_channel = guild.get_channel(channel_id)
        if not target_channel or not isinstance(target_channel, discord.TextChannel):
            return {"status": "error", "message": "Target channel not found or is not a text channel."}

        role = guild.get_role(role_id)
        if not role:
            return {"status": "error", "message": f"Role with ID {role_id} not found."}

        # Send initial panel message
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.purple()
        )

        try:
            # We first register a dummy message to get its ID, or we post the message first
            # Send message first
            if type_ == "reaction":
                msg = await target_channel.send(embed=embed)
                await msg.add_reaction(emoji)
            elif type_ == "button":
                # Create a temporary view to test
                temp_mapping = [{
                    "guild_id": guild.id,
                    "message_id": 0,
                    "emoji": emoji,
                    "role_id": role_id,
                    "group_name": group_name
                }]
                # Setup mapping details in db first then generate view
                # Wait, we need to create the DB entries first so build_persistent_view works
                # Let's save setup config with placeholder message_id, then send, then update DB!
                # Or we can create the setup config with message_id=0, save roles, send message with view, update message_id in db.
                # Let's post a placeholder, then save setup, then edit message with proper view!
                msg = await target_channel.send(embed=embed)
            elif type_ == "select":
                msg = await target_channel.send(embed=embed)
            else:
                return {"status": "error", "message": f"Invalid type '{type_}'."}

            message_id = msg.id

            # Save to Database
            setup = await self.rr_service.create_setup(
                message_id=message_id,
                guild_id=guild.id,
                channel_id=channel_id,
                title=title,
                description=description,
                group_name=group_name,
                type_=type_
            )
            await self.rr_service.add_role_mapping(guild.id, message_id, emoji, role_id, group_name)

            # If button or select, we re-fetch the view from service (which reads database) and edit the message to attach the view!
            if type_ in ["button", "select"]:
                view = await self.rr_service.build_persistent_view(setup)
                if view:
                    await msg.edit(view=view)
                    self.services.get(discord.Client).add_view(view, message_id=message_id)

            return {
                "status": "success",
                "message": f"Successfully created reaction role message (ID: {message_id}) in channel {target_channel.name}.",
                "type": type_,
                "group_name": group_name
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
