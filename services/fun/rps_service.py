"""Rock Paper Scissors Service."""

import random
from typing import Dict
from services.base_service import BaseService

class RPSService(BaseService):
    """Calculates results for rock paper scissors."""

    async def play(self, user_choice: str) -> Dict[str, str]:
        user_choice_clean = user_choice.lower().strip()
        choices = ["rock", "paper", "scissors"]
        if user_choice_clean not in choices:
            raise ValueError("Choice must be 'rock', 'paper', or 'scissors'.")

        bot_choice = random.choice(choices)
        
        if user_choice_clean == bot_choice:
            result = "tie"
        elif (
            (user_choice_clean == "rock" and bot_choice == "scissors") or
            (user_choice_clean == "paper" and bot_choice == "rock") or
            (user_choice_clean == "scissors" and bot_choice == "paper")
        ):
            result = "win"
        else:
            result = "loss"

        return {
            "user": user_choice_clean,
            "bot": bot_choice,
            "result": result
        }
