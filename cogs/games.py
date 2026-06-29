"""Mini-games and Leaderboard Cog for NoSpaceFGK."""

import asyncio
import random
import time
from typing import Dict, List, Optional
import discord
from discord import app_commands
from discord.ext import commands

from decorators.command_dec import guild_only_command
from services.fun.game_service import GameService
from repositories.leaderboard_repository import LeaderboardRepository
from utils.embeds import success_embed, error_embed, info_embed
from utils.logger import logger

# ==================== TIC TAC TOE GAME VIEW ====================
class TicTacToeButton(discord.ui.Button["TicTacToeView"]):
    def __init__(self, x: int, y: int) -> None:
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction) -> None:
        assert self.view is not None
        view = self.view
        
        # Check turn
        current_player = view.players[view.turn_idx]
        if interaction.user.id != current_player:
            return await interaction.response.send_message("It's not your turn!", ephemeral=True)
            
        # Make move
        symbol = "X" if view.turn_idx == 0 else "O"
        self.label = symbol
        self.style = discord.ButtonStyle.primary if symbol == "X" else discord.ButtonStyle.success
        self.disabled = True
        view.board[self.y][self.x] = symbol
        
        # Check winner
        winner = view.check_winner()
        if winner:
            view.disable_all()
            winner_user = view.bot.get_user(current_player)
            await view.service.end_session(view.session_id, winner_id=current_player)
            await interaction.response.edit_message(
                content=f"🎉 **{winner_user.mention} ({symbol}) has won!**",
                view=view
            )
            return

        # Check tie
        if view.is_board_full():
            view.disable_all()
            await view.service.end_session(view.session_id, winner_id=None)
            await interaction.response.edit_message(
                content="🤝 **It's a tie!**",
                view=view
            )
            return

        # Switch turn
        view.turn_idx = 1 - view.turn_idx
        next_player = view.bot.get_user(view.players[view.turn_idx])
        next_symbol = "X" if view.turn_idx == 0 else "O"
        
        await interaction.response.edit_message(
            content=f"🎮 **Tic-Tac-Toe** | Turn: {next_player.mention} ({next_symbol})",
            view=view
        )

class TicTacToeView(discord.ui.View):
    def __init__(self, bot: commands.Bot, service: GameService, session_id: str, player1_id: int, player2_id: int) -> None:
        super().__init__(timeout=300)
        self.bot = bot
        self.service = service
        self.session_id = session_id
        self.players = [player1_id, player2_id]
        self.turn_idx = 0
        self.board = [["" for _ in range(3)] for _ in range(3)]
        
        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_winner(self) -> Optional[str]:
        # Rows
        for row in self.board:
            if row[0] == row[1] == row[2] != "":
                return row[0]
        # Columns
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != "":
                return self.board[0][col]
        # Diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != "":
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != "":
            return self.board[0][2]
        return None

    def is_board_full(self) -> bool:
        return all(self.board[y][x] != "" for y in range(3) for x in range(3))

    def disable_all(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    async def on_timeout(self) -> None:
        self.disable_all()
        await self.service.end_session(self.session_id, aborted=True)
        # We can't easily edit the original message directly here without the interaction reference, 
        # but the game session is closed in memory.


# ==================== TRIVIA GAME VIEW ====================
class TriviaButton(discord.ui.Button["TriviaView"]):
    def __init__(self, label: str, custom_id: str) -> None:
        super().__init__(style=discord.ButtonStyle.secondary, label=label, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction) -> None:
        assert self.view is not None
        view = self.view
        
        if interaction.user.id not in view.players:
            return await interaction.response.send_message("You are not part of this game!", ephemeral=True)

        if view.answered:
            return # Already answered
            
        view.answered = True
        view.disable_all()
        
        is_correct = self.custom_id == "correct"
        winner_id = interaction.user.id if is_correct else None
        
        if is_correct:
            self.style = discord.ButtonStyle.success
            content = f"✅ **Correct!** {interaction.user.mention} got the right answer: **{view.correct_answer}**!"
        else:
            self.style = discord.ButtonStyle.danger
            content = f"❌ **Incorrect!** {interaction.user.mention} chose wrong. The correct answer was **{view.correct_answer}**."
            
        await view.service.end_session(view.session_id, winner_id=winner_id)
        await interaction.response.edit_message(content=content, view=view)

class TriviaView(discord.ui.View):
    def __init__(self, service: GameService, session_id: str, players: List[int], correct_answer: str, incorrect_answers: List[str]) -> None:
        super().__init__(timeout=60)
        self.service = service
        self.session_id = session_id
        self.players = players
        self.correct_answer = correct_answer
        self.answered = False
        
        answers = [(correct_answer, "correct")] + [(ans, f"wrong_{i}") for i, ans in enumerate(incorrect_answers)]
        random.shuffle(answers)
        
        for ans_text, cid in answers:
            self.add_item(TriviaButton(label=ans_text[:80], custom_id=cid))

    def disable_all(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True


# ==================== COG DEFINITION ====================
class GamesCog(commands.Cog, name="Games"):
    """Cog for hosting interactive mini-games and showing leaderboards."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.service: GameService = bot.container.get(GameService)
        self.leaderboards: LeaderboardRepository = bot.container.get(LeaderboardRepository)
        logger.info("GamesCog fully initialized.")

    @app_commands.command(name="games", description="Start an interactive mini-game or view rankings.")
    @app_commands.describe(
        action="Select action: 'start' or 'leaderboard'",
        game_type="Required if start: 'tictactoe' or 'trivia'",
        opponent="Optional opponent for multiplayer games (e.g. TicTacToe)"
    )
    @guild_only_command()
    async def games_cmd(
        self,
        interaction: discord.Interaction,
        action: str,
        game_type: Optional[str] = None,
        opponent: Optional[discord.Member] = None
    ) -> None:
        action_clean = action.lower().strip()
        
        if action_clean == "leaderboard":
            await interaction.response.defer()
            try:
                top = await self.leaderboards.get_top_users(interaction.guild_id, "wins", limit=10)
                if not top:
                    return await interaction.followup.send(embed=info_embed("Game Leaderboard 🏆", "No statistics recorded yet. Play games to rank!"))
                
                desc = []
                for entry in top:
                    user = self.bot.get_user(entry.user_id) or await self.bot.fetch_user(entry.user_id)
                    username = user.name if user else f"User ID {entry.user_id}"
                    desc.append(f"**#{entry.rank}** | {username} — `{entry.value} wins`")
                    
                embed = info_embed("Server Gaming Leaderboard 🏆", "\n".join(desc))
                await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(embed=error_embed("Leaderboard Error", str(e)))
            return

        # START ACTION
        if not game_type:
            return await interaction.response.send_message(embed=error_embed("Game Error", "Please specify a `game_type` to start a game."), ephemeral=True)
            
        game_clean = game_type.lower().strip()
        
        if game_clean == "tictactoe":
            if not opponent:
                return await interaction.response.send_message(embed=error_embed("Tic-Tac-Toe Error", "You must specify an `opponent` to play Tic-Tac-Toe."), ephemeral=True)
            if opponent.bot:
                return await interaction.response.send_message(embed=error_embed("Tic-Tac-Toe Error", "You cannot play games against bots!"), ephemeral=True)
            if opponent.id == interaction.user.id:
                return await interaction.response.send_message(embed=error_embed("Tic-Tac-Toe Error", "You cannot play against yourself!"), ephemeral=True)
                
            try:
                session = await self.service.create_session(
                    guild_id=interaction.guild_id,
                    channel_id=interaction.channel_id,
                    game_type="tictactoe",
                    players=[interaction.user.id, opponent.id]
                )
                
                view = TicTacToeView(self.bot, self.service, session.id, interaction.user.id, opponent.id)
                await interaction.response.send_message(
                    content=f"🎮 **Tic-Tac-Toe** | Turn: {interaction.user.mention} (X)",
                    view=view
                )
            except ValueError as e:
                await interaction.response.send_message(embed=error_embed("Lobby Conflict", str(e)), ephemeral=True)
                
        elif game_clean == "trivia":
            # For Trivia, let's fetch a question from a small curated pool
            trivia_pool = [
                {
                    "question": "What is the primary scripting language used for web development?",
                    "correct": "JavaScript",
                    "incorrect": ["Python", "C++", "Java"]
                },
                {
                    "question": "What does SQL stand for?",
                    "correct": "Structured Query Language",
                    "incorrect": ["System Query Language", "Structured Question Language", "System Question Link"]
                },
                {
                    "question": "Which of these is not a relational database?",
                    "correct": "MongoDB",
                    "incorrect": ["PostgreSQL", "MySQL", "SQLite"]
                }
            ]
            q = random.choice(trivia_pool)
            
            try:
                session = await self.service.create_session(
                    guild_id=interaction.guild_id,
                    channel_id=interaction.channel_id,
                    game_type="trivia",
                    players=[interaction.user.id]
                )
                
                view = TriviaView(
                    service=self.service,
                    session_id=session.id,
                    players=[interaction.user.id],
                    correct_answer=q["correct"],
                    incorrect_answers=q["incorrect"]
                )
                
                embed = info_embed("Trivia Challenge 🧠", q["question"])
                await interaction.response.send_message(embed=embed, view=view)
            except ValueError as e:
                await interaction.response.send_message(embed=error_embed("Lobby Conflict", str(e)), ephemeral=True)
        else:
            await interaction.response.send_message(embed=error_embed("Game Error", f"Unsupported game type: `{game_type}`."), ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GamesCog(bot))
