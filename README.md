# NoSpaceFGK Discord Bot

A modular, production-ready, feature-rich Discord assistant built with Python 3.12+ and `discord.py` 2.x. 

This project is engineered with stability, strict configurations, and clean architecture patterns to support scale-up to 100+ slash commands, dynamic data storage, AI integrations, and containerized cloud deployment.

---

## Project Overview

**NoSpaceFGK** is designed using a decoupled plugin (Cog) and event handler architecture, minimizing global mutable state and maximizing system reliability. All custom features are structured as independent extensions loaded dynamically at runtime.

---

## Command & Framework Features (Phase 2)

*   **centralized Error Handling**: Custom Command Tree error mapping in `bot.py` translates standard Discord exceptions (like cooldowns, missing permissions, checks failures) into clean, ephemeral error embeds.
*   **Reusable UI Components**: Defines a standardized confirmation dialog view (`ConfirmationView`) and an abstract paginator (`PaginationView`) with Home, Previous, Next, and Close controls in the `ui/` package.
*   **Slash Command Decorators**: Simplifies checks using custom wrappers (`@is_owner()`, `@is_premium()`, `@cooldown_command()`, `@guild_only_command()`, and `@permission_check()`).
*   **Autocomplete Query Framework**: Modularizes autocomplete search query filtering under `autocomplete/query_utils.py` to support dynamic slash choices.
*   **Static & Relative Helpers**: Exposes common text converters, Discord Snowflake to DateTime converters, markdown escaping, and relative timestamp makers in `utils/helpers.py`.

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
├── cogs/                 # Modular extension components (Cogs)
│   ├── ai.py             # AI Assistant placeholders
│   ├── memes.py          # Memes placeholders
│   ├── moderation.py     # Moderation placeholders
│   ├── music.py          # Music streaming placeholders
│   ├── owner.py          # Owner administrative tools (slash command /sync)
│   └── utility.py        # General and Utility slash commands (ping, serverinfo, help pagination)
├── events/               # Event listener package
│   ├── __init__.py       # Package initializer and setup hooks
│   ├── ready.py          # Dynamic gateway connection events
│   ├── members.py        # Dynamic member lifecycle handlers
│   ├── messages.py       # Dynamic message listeners and command completion loggers
│   └── errors.py         # Prefix command execution error logs
├── checks/               # Permission logic evaluations and owner predicates
├── decorators/           # Reusable command check wrappers
├── autocomplete/         # Choice query parsing filters
├── ui/                   # Reusable UI component views and paginated view templates
├── services/             # Empty placeholder layer for business logic coordinators
├── repositories/         # Empty placeholder layer for data storage adapters
├── models/               # Empty placeholder layer for domain concepts
├── schemas/              # Empty placeholder layer for validation contracts
└── utils/                # Utility package for shared resources
    ├── __init__.py       # Package initializer
    ├── constants.py      # Read-only design system colors and paths
    ├── embeds.py         # Standardized embed template wrappers with footer styling
    ├── exceptions.py     # Custom exception classes
    ├── helpers.py        # Snowflake converters, relative date strings, duration formatters
    └── logger.py         # Dual-channel Rich console and TimedRotatingFile logging
```

---

## System Requirements

*   **Python**: `3.12` or higher
*   **Libraries**: Listed in `requirements.txt` (`discord.py`, `python-dotenv`, `aiofiles`, `PyYAML`, `rich`)

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

5.  **Start the Application**:
    ```bash
    python launcher.py
    ```

---

## Development Roadmap

*   [x] **Phase 1: Foundation & Architecture** (Structure, Configuration, Logging, Launchers, Event Handlers).
*   [x] **Phase 2: Core Discord Framework** (Slash command systems, dynamic help directory, central error handling, UI Views, decorators).
*   [ ] **Phase 3: Music & AI Services** (Voice connection, audio player, AI API interface).
*   [ ] **Phase 4: Advanced Features** (Moderation, Memes, Web dashboard, API hooks).
*   [ ] **Phase 5: Deployments & Operations** (Docker, Github actions, CI/CD, production scale tests).

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

