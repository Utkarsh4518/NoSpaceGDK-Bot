# NoSpaceFGK Discord Bot

A modular, production-ready, feature-rich Discord assistant built with Python 3.12+ and `discord.py` 2.x. 

This project is engineered with stability, strict configurations, and clean architecture patterns to support scale-up to 100+ slash commands, dynamic data storage, AI integrations, and containerized cloud deployment.

---

## Project Overview

**NoSpaceFGK** is designed using a decoupled plugin (Cog) and event handler architecture, minimizing global mutable state and maximizing system reliability. All custom features are structured as independent extensions loaded dynamically at runtime.

---

## Command & Framework Features (Phase 2)

*   **Centralized Error Handling**: Custom Command Tree error mapping in `bot.py` translates standard Discord exceptions (like cooldowns, missing permissions, checks failures) into clean, ephemeral error embeds.
*   **Reusable UI Components**: Defines a standardized confirmation dialog view (`ConfirmationView`) and an abstract paginator (`PaginationView`) with Home, Previous, Next, and Close controls in the `ui/` package.
*   **Slash Command Decorators**: Simplifies checks using custom wrappers (`@is_owner()`, `@is_premium()`, `@cooldown_command()`, `@guild_only_command()`, and `@permission_check()`).
*   **Autocomplete Query Framework**: Modularizes autocomplete search query filtering under `autocomplete/query_utils.py` to support dynamic slash choices.
*   **Static & Relative Helpers**: Exposes common text converters, Discord Snowflake to DateTime converters, markdown escaping, and relative timestamp makers in `utils/helpers.py`.

---

## Backend Architecture & Data Layer (Phase 3)

The backend layer coordinates data storage, cache lookups, configuration setups, and business operations under strict architecture boundary rules:

### 1. Dependency Graph (Layer Rules)
```text
  [ Cogs / Discord Tree ]
            │
            ▼
     [ Service Layer ]        <─── [ Cache Service ]
            │
            ▼
    [ Repository Layer ]      <─── [ Validation Schemas ]
            │
            ▼
    [ Database Manager ]      <─── [ Migration Runner ]
            │
            ▼
       [ aiosqlite ]
```
*   **Layer Rule**: Higher layers must never bypass lower layers (e.g., Cogs must never execute SQL queries or access Repositories directly; they must call Services).
*   **Dependency Injection**: Instantiated lazily during bot startup in `bot.py` via `ServiceContainer` without third-party frameworks.

### 2. Database Schema
NoSpaceFGK uses SQLite with WAL (Write-Ahead Logging) mode and foreign keys enabled.
*   `schema_version` (tracks migration history)
    *   `version` (INTEGER PRIMARY KEY)
    *   `applied_at` (TIMESTAMP)
*   `guilds` (server configurations)
    *   `id` (INTEGER PRIMARY KEY)
    *   `prefix` (TEXT, default `!`)
    *   `created_at` (TIMESTAMP)
*   `users` (member accounts)
    *   `id` (INTEGER PRIMARY KEY)
    *   `username` (TEXT)
    *   `is_premium` (INTEGER, default `0`)
    *   `created_at` (TIMESTAMP)
*   `bot_settings` (global variables)
    *   `key` (TEXT PRIMARY KEY)
    *   `value` (TEXT)
    *   `updated_at` (TIMESTAMP)
*   `command_usages` (usage metrics)
    *   `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
    *   `user_id` (INTEGER)
    *   `guild_id` (INTEGER NULL)
    *   `command_name` (TEXT)
    *   `execution_time` (REAL)
    *   `status` (TEXT)
    *   `executed_at` (TIMESTAMP)
*   `audit_logs` (security trails)
    *   `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
    *   `action` (TEXT)
    *   `user_id` (INTEGER)
    *   `details` (TEXT NULL)
    *   `timestamp` (TIMESTAMP)

### 3. Caching System
*   An in-memory dictionary-backed `CacheService` with custom TTL settings per-key, stale item invalidation, and hit/miss statistics logging.

---

## Music Engine Architecture (Phase 4)

NoSpaceFGK includes a fully decoupled, provider-agnostic music playback engine. It isolates domain models, queuing states, and voice connections from external stream downloaders (such as YouTube or Spotify) to support multiple audio adapters.

### 1. Class Relationships (UML Layout)
```text
                 ┌──────────────────┐
                 │   MusicService   │
                 └────────┬─────────┘
                          │
         ┌────────────────┴───────────────┐
         ▼                                ▼
┌─────────────────┐             ┌──────────────────┐
│  PlayerManager  │             │ ProviderManager  │
└────────┬────────┘             └────────┬─────────┘
         │ (manages)                     │ (resolves)
         ▼                               ▼
┌─────────────────┐             ┌──────────────────┐
│ BaseMusicPlayer │             │BaseMusicProvider │
└────────┬────────┘             └────────┬─────────┘
         │ (coordinates)
         ├──────────────────────┬──────────────────────┐
         ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  QueueManager   │    │  VoiceManager   │    │  AudioManager   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2. Music Schema Definitions (Migration v3)
*   `music_tracks` (registers validated song data)
    *   `uuid` (TEXT PRIMARY KEY)
    *   `title` (TEXT)
    *   `artist` (TEXT)
    *   `duration` (REAL)
    *   `thumbnail` (TEXT NULL)
    *   `provider` (TEXT)
    *   `url` (TEXT)
    *   `requested_by` (INTEGER)
    *   `isrc` (TEXT NULL)
    *   `metadata` (TEXT json)
    *   `added_at` (TIMESTAMP)
*   `playlists` (custom collections)
    *   `uuid` (TEXT PRIMARY KEY)
    *   `name` (TEXT)
    *   `owner_id` (INTEGER)
    *   `updated_at` (TIMESTAMP)
*   `playlist_tracks` (many-to-many playlist mappings)
    *   `playlist_uuid` (TEXT FOREIGN KEY)
    *   `track_uuid` (TEXT FOREIGN KEY)
    *   `position` (INTEGER)
*   `playback_history` (server statistics)
    *   `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
    *   `guild_id` (INTEGER)
    *   `track_uuid` (TEXT FOREIGN KEY)
    *   `played_by` (INTEGER)
    *   `played_at` (TIMESTAMP)

---

## Directory Structure

```text
NoSpaceFGK/
├── bot.py                # Custom commands.Bot wrapper and extension management
├── launcher.py           # Application entry point, environment verification, fatal-error handler
├── config.py             # dotenv configuration parsing and validation schema
├── requirements.txt      # Exact project dependencies
├── README.md             # Project documentation and architectural overview
├── .gitignore            # Git exclusion rules
├── .env.example          # Sample environment variables
├── logs/                 # Active file logging outputs (daily rotating)
├── assets/               # Non-code assets (images, designs, presets)
├── data/                 # Local data storage placeholders (e.g. SQLite database files)
├── docs/                 # Software design specifications and manuals
├── tests/                # Automated testing suites
├── database/             # Database connection, schemas, migrations and seeder scripts
│   ├── connection.py     # Connection wrapper with WAL and foreign key configuration
│   ├── schema.py         # Versioned SQL scripts for schema alterations (v1, v2, v3)
│   ├── migration.py      # Migration runner checking version histories
│   └── seed.py           # Populates initial values when databases are empty
├── models/               # Domain dataclasses (User, Guild, BotSettings, Track, Playlist)
├── schemas/              # Payload validation contracts (GuildSchema, UserSchema, SettingsSchema)
├── repositories/         # Persistent layer mapping SQL rows to domain models
│   ├── base_repository.py # Injects DatabaseManager
│   ├── guild_repository.py # Guild CRUD actions
│   ├── user_repository.py  # Member profile CRUD actions
│   ├── settings_repository.py # Global settings CRUD actions
│   ├── usage_repository.py # Writes command usage audits
│   ├── music_repository.py # Saves song details
│   ├── playlist_repository.py # Saves custom user playlists
│   └── history_repository.py # Tracks guild play histories
├── providers/             # Placeholders for music metadata source retrievers
│   ├── base_provider.py   # Abstract provider base class interface
│   ├── youtube_provider.py # YouTube adapter raising NotImplementedError
│   ├── spotify_provider.py # Spotify adapter raising NotImplementedError
│   └── soundcloud_provider.py # SoundCloud adapter raising NotImplementedError
├── services/             # Business coordinators and dependency injection providers
│   ├── service_container.py # Thread-safe DI service locator registry
│   ├── cache_service.py   # In-memory TTL key-value caching service
│   ├── bot_service.py     # Controls configurations and prefixes
│   ├── config_service.py  # Bridges config properties
│   ├── logging_service.py # Intermediary audit trail logger
│   ├── response_service.py # Themed layout responses builder
│   └── music/             # Modular abstract music engines
│       ├── base_player.py # Integrates audio, voice, and queue operations
│       ├── player_manager.py # Coordinates active guild player lifecycles
│       ├── queue_manager.py # Async locked track queue controller
│       ├── track_manager.py # Caches search data and resolved tracks
│       ├── voice_manager.py # Manages voice client connections
│       ├── audio_manager.py # Placeholders for volumes and filters adjustments
│       ├── provider_manager.py # Registers active provider modules
│       └── music_service.py # Root facade service coordinator
├── cogs/                 # Modular extension components (Cogs)
│   ├── ai.py             # AI Assistant placeholders
│   ├── memes.py          # Memes placeholders
│   ├── moderation.py     # Moderation placeholders
│   ├── music.py          # Music streaming placeholders
│   ├── owner.py          # Owner administrative tools
│   └── utility.py        # General utilities
├── events/               # Event listener package
│   ├── __init__.py       # Package initializer and setup hooks
│   └── listeners.py      # Core Discord gateway event handlers
└── utils/                # Utility package for shared resources
    ├── __init__.py       # Package initializer
    ├── constants.py      # Read-only design system colors and paths
    ├── embeds.py         # Standardized embed template wrappers
    ├── exceptions.py     # Custom exception classes
    ├── helpers.py        # Snowflake converters, relative date strings, duration formatters
    └── logger.py         # Dual-channel Rich console and TimedRotatingFile logging
```

---

## System Requirements

*   **Python**: `3.12` or higher
*   **Libraries**: Listed in `requirements.txt` (`discord.py`, `python-dotenv`, `aiofiles`, `PyYAML`, `rich`, `aiosqlite`)

---

## Installation & Setup

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/yourusername/NoSpaceFGK.git
    cd NoSpaceFGK
    ```

2.  **Set Up a Virtual Environment**:
    ```bash
    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    # macOS/Linux:
    source .venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    Copy `.env.example` to a new file named `.env`:
    ```bash
    cp .env.example .env
    ```
    Populate the variables with your credentials:
    *   `DISCORD_TOKEN`: Your Discord Developer Application token.
    *   `CLIENT_ID`: Your Discord Bot Client/Application ID.
    *   `OWNER_IDS`: Comma-separated list of developer Discord IDs.
    *   `DEVELOPMENT_GUILD_ID`: Optional guild ID for command synchronization during testing.
    *   `DATABASE_PATH`: SQLite database file path (Default: `data/bot.db`).
    *   `CACHE_TTL`: Cache entry Time-To-Live in seconds (Default: `300`).

5.  **Start the Application**:
    ```bash
    python launcher.py
    ```

---

## Development Roadmap

*   [x] **Phase 1: Foundation & Architecture** (Structure, Configuration, Logging, Launchers, Event Handlers).
*   [x] **Phase 2: Core Discord Framework** (Slash command systems, dynamic help directory, central error handling, UI Views, decorators).
*   [x] **Phase 3: Backend Architecture & Data Layer** (aiosqlite database, migrations, repositories, validation schemas, caching, DI).
*   [x] **Phase 4: Music Engine Architecture** (Provider-agnostic player, thread-safe queue, audio states, voice connection manager).
*   [ ] **Phase 5: Music & AI Services** (YouTube/Spotify connectors, audio player, AI API interface).
*   [ ] **Phase 6: Advanced Features** (Moderation, Memes, Web dashboard, API hooks).
*   [ ] **Phase 7: Deployments & Operations** (Docker, Github actions, CI/CD, production scale tests).

---

## License

Distributed under the MIT License. See `LICENSE` in the future for more information.

---

## Contribution Guidelines

1.  Create an issue discussing planned changes.
2.  Fork the repository.
3.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
4.  Write comprehensive tests. Ensure all code follows PEP8 standards, has type hints, and includes descriptive docstrings.
5.  Commit changes (`git commit -m 'Add some AmazingFeature'`).
6.  Push to the branch (`git push origin feature/AmazingFeature`).
7.  Open a Pull Request.
