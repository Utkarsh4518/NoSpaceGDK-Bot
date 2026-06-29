"""Validation schemas for the NoSpaceFGK bot.

Ensures payload parameters are correct and valid before being written
to persistent repositories.
"""

from typing import Any, Dict
from schemas.exceptions import ValidationError


class SettingsSchema:
    """Schema to validate Bot Settings inputs."""

    @staticmethod
    def validate(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate BotSettings properties.

        Args:
            data: Raw dictionary payload.

        Returns:
            Validated payload dictionary.

        Raises:
            ValidationError: If validation fails.
        """
        key = data.get("key")
        if not key or not isinstance(key, str) or not key.strip():
            raise ValidationError("Setting 'key' must be a non-empty string.")

        value = data.get("value")
        if value is None or not isinstance(value, str):
            raise ValidationError("Setting 'value' must be a valid string.")

        return {"key": key.strip(), "value": value}


class GuildSchema:
    """Schema to validate Guild configuration inputs."""

    @staticmethod
    def validate(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Guild properties.

        Args:
            data: Raw dictionary payload.

        Returns:
            Validated payload dictionary.

        Raises:
            ValidationError: If validation fails.
        """
        guild_id = data.get("id")
        if guild_id is None or not isinstance(guild_id, int):
            raise ValidationError("Guild 'id' must be a valid integer.")

        prefix = data.get("prefix", "!")
        if not isinstance(prefix, str) or not prefix.strip():
            raise ValidationError("Guild 'prefix' must be a non-empty string.")
        if len(prefix) > 5:
            raise ValidationError("Guild 'prefix' cannot exceed 5 characters in length.")

        return {"id": guild_id, "prefix": prefix.strip()}


class UserSchema:
    """Schema to validate User domain inputs."""

    @staticmethod
    def validate(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate User properties.

        Args:
            data: Raw dictionary payload.

        Returns:
            Validated payload dictionary.

        Raises:
            ValidationError: If validation fails.
        """
        user_id = data.get("id")
        if user_id is None or not isinstance(user_id, int):
            raise ValidationError("User 'id' must be a valid integer.")

        username = data.get("username")
        if username is not None and not isinstance(username, str):
            raise ValidationError("User 'username' must be a string or None.")

        is_premium = data.get("is_premium", False)
        # Handle conversion from int to bool if loaded from SQLite
        if isinstance(is_premium, int) and not isinstance(is_premium, bool):
            is_premium = bool(is_premium)
        if not isinstance(is_premium, bool):
            raise ValidationError("User 'is_premium' must be a boolean flag.")

        return {
            "id": user_id,
            "username": username.strip() if username else None,
            "is_premium": is_premium
        }


class ResponseSchema:
    """Schema to validate service operation response contracts."""

    @staticmethod
    def validate(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate unified Service Response parameters.

        Args:
            data: Raw dictionary payload.

        Returns:
            Validated payload dictionary.

        Raises:
            ValidationError: If validation fails.
        """
        success = data.get("success")
        if success is None or not isinstance(success, bool):
            raise ValidationError("Response 'success' status must be a boolean flag.")

        error = data.get("error")
        if error is not None and not isinstance(error, str):
            raise ValidationError("Response 'error' message must be a string or None.")

        result_data = data.get("data")
        if result_data is not None and not isinstance(result_data, dict):
            raise ValidationError("Response 'data' must be a dictionary or None.")

        return {"success": success, "error": error, "data": result_data}
