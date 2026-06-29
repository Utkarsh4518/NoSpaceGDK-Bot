"""Token and cost estimation manager for AI services."""

import datetime
from typing import Dict, Optional
from repositories.base_repository import BaseRepository
from database.connection import DatabaseManager
from utils.logger import logger


class TokenManager(BaseRepository):
    """Tracks token consumption per provider/model and logs estimated costs.

    Pricing structure based on per-million token rates:
        - gpt-4o-mini:             Input $0.15, Output $0.60
        - gpt-4o:                  Input $2.50, Output $10.00
        - gemini-1.5-flash:        Input $0.075, Output $0.30
        - gemini-1.5-pro:          Input $1.25, Output $5.00
        - claude-3-5-sonnet-latest: Input $3.00, Output $15.00
        - claude-3-5-haiku-latest:  Input $0.80, Output $4.00
        - ollama/free models:      $0.00
    """

    PRICING_MAP: Dict[str, Dict[str, float]] = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
        "claude-3-5-sonnet-latest": {"input": 3.00, "output": 15.00},
        "claude-3-5-haiku-latest": {"input": 0.80, "output": 4.00},
    }

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize TokenManager with a database link."""
        super().__init__(db)

    def estimate_cost(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate transaction costs using standard rate cards.

        Args:
            provider: AI backend provider name.
            model: Model identifier.
            prompt_tokens: Input tokens.
            completion_tokens: Generated tokens.

        Returns:
            Cost estimation in USD.
        """
        # Providers like Ollama or free models cost nothing
        if "free" in model.lower() or provider.lower() == "ollama":
            return 0.0

        # Try to find model in map (allowing partial substring matches)
        rates = None
        for key, value in self.PRICING_MAP.items():
            if key in model.lower():
                rates = value
                break

        if not rates:
            # Baseline default (e.g. gpt-4o-mini rates)
            rates = self.PRICING_MAP["gpt-4o-mini"]

        prompt_cost = (prompt_tokens / 1_000_000) * rates["input"]
        completion_cost = (completion_tokens / 1_000_000) * rates["output"]
        return prompt_cost + completion_cost

    async def log_usage(
        self,
        guild_id: Optional[int],
        user_id: int,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Persist a token usage record to database.

        Args:
            guild_id: Optional Discord Guild snowflake.
            user_id: Discord User snowflake.
            provider: Provider name.
            model: Model name.
            prompt_tokens: Prompt token count.
            completion_tokens: Completion token count.

        Returns:
            Estimated cost of this request.
        """
        cost = self.estimate_cost(provider, model, prompt_tokens, completion_tokens)
        total = prompt_tokens + completion_tokens

        query = """
            INSERT INTO ai_token_usage (guild_id, user_id, provider, model, prompt_tokens, completion_tokens, total_tokens, estimated_cost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        await self.db.execute(query, (
            guild_id, user_id, provider, model, prompt_tokens, completion_tokens, total, cost
        ))
        await self.db.commit()

        logger.info(
            f"Token manager: Logged {total} tokens for User {user_id} "
            f"on {provider}/{model} (Cost: ${cost:.6f})."
        )
        return cost

    async def get_statistics(self, user_id: Optional[int] = None, guild_id: Optional[int] = None) -> Dict[str, Any]:
        """Aggregate token counts and cost stats.

        Args:
            user_id: Optional User ID filter.
            guild_id: Optional Guild ID filter.

        Returns:
            Dict containing token metrics and aggregate cost.
        """
        clauses = []
        params = []

        if user_id:
            clauses.append("user_id = ?")
            params.append(user_id)
        if guild_id:
            clauses.append("guild_id = ?")
            params.append(guild_id)

        where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"""
            SELECT SUM(prompt_tokens), SUM(completion_tokens), SUM(total_tokens), SUM(estimated_cost), COUNT(*)
            FROM ai_token_usage
            {where_clause};
        """
        
        async with self.db.connection.execute(query, params) as cursor:
            row = await cursor.fetchone()
            if not row or row[2] is None:
                return {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "request_count": 0
                }

            return {
                "prompt_tokens": row[0],
                "completion_tokens": row[1],
                "total_tokens": row[2],
                "total_cost": round(row[3], 6),
                "request_count": row[4]
            }
