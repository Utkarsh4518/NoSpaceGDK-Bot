# Models Layer

## Responsibility
The **Models** layer defines the core objects and domain entities that model our business domain (e.g. `User`, `Playlist`, `GuildConfig`, `MemePreset`).

## Guidelines
*   Domain models should be pure Python structures (such as dataclasses or basic objects) containing fields and operations relevant only to that entity's self-contained rules.
*   Models are data-centric but behavior-rich where it makes sense (e.g., checking if a user subscription is expired).
*   Avoid tying domain models directly to database models or Discord models, maintaining clean encapsulation.
