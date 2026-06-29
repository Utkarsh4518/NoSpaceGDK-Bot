"""Automod rules Repository."""

import json
from typing import List, Optional
from models.automod import AutomodRuleModel
from repositories.base_repository import BaseRepository

class AutomodRepository(BaseRepository):
    """Handles SQL queries for automod rule configurations."""

    async def get_rules_for_guild(self, guild_id: int) -> List[AutomodRuleModel]:
        query = """
            SELECT id, guild_id, rule_type, config, is_enabled, created_at
            FROM automod_rules
            WHERE guild_id = ?;
        """
        rules = []
        async with self.db.connection.execute(query, (guild_id,)) as cursor:
            async for row in cursor:
                import datetime
                created_at_dt = datetime.datetime.fromisoformat(row[5])
                rules.append(AutomodRuleModel(
                    id=row[0],
                    guild_id=row[1],
                    rule_type=row[2],
                    config=row[3],
                    is_enabled=bool(row[4]),
                    created_at=created_at_dt
                ))
        return rules

    async def get_rule(self, guild_id: int, rule_type: str) -> Optional[AutomodRuleModel]:
        query = """
            SELECT id, guild_id, rule_type, config, is_enabled, created_at
            FROM automod_rules
            WHERE guild_id = ? AND rule_type = ?;
        """
        async with self.db.connection.execute(query, (guild_id, rule_type)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            import datetime
            created_at_dt = datetime.datetime.fromisoformat(row[5])
            return AutomodRuleModel(
                id=row[0],
                guild_id=row[1],
                rule_type=row[2],
                config=row[3],
                is_enabled=bool(row[4]),
                created_at=created_at_dt
            )

    async def create_or_update_rule(self, guild_id: int, rule_type: str, config: dict, is_enabled: bool = True) -> AutomodRuleModel:
        config_str = json.dumps(config)
        existing = await self.get_rule(guild_id, rule_type)
        
        if existing:
            query = "UPDATE automod_rules SET config = ?, is_enabled = ? WHERE guild_id = ? AND rule_type = ?;"
            await self.db.execute(query, (config_str, int(is_enabled), guild_id, rule_type))
        else:
            query = "INSERT INTO automod_rules (guild_id, rule_type, config, is_enabled) VALUES (?, ?, ?, ?);"
            await self.db.execute(query, (guild_id, rule_type, config_str, int(is_enabled)))
            
        await self.db.commit()
        updated = await self.get_rule(guild_id, rule_type)
        if not updated:
            raise RuntimeError("Failed to retrieve automod rule after save.")
        return updated
