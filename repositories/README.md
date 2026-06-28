# Repositories Layer

## Responsibility
The **Repositories** layer abstracts data storage and retrieval. It encapsulates the queries, connection management, and mapping from raw database records to Python objects.

## Guidelines
*   All database SQL scripts, SQLite connection handlers, PostgreSQL bindings, and cache operations (Redis) live here.
*   Services query repositories for objects (e.g. `get_guild_settings(guild_id)`) rather than running raw SQL.
*   This pattern allows changing database backends (e.g., migrating from SQLite to PostgreSQL) with zero changes to business logic services.
