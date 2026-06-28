# Services Layer

## Responsibility
The **Services** layer houses the core business logic of the application. It acts as the coordinator between the presentation layer (Discord Bot Cogs/Events) and the data layer (Repositories).

## Guidelines
*   All business logic (such as calculating streaming queues, parsing AI contexts, or evaluating spam threshold rules) should live here.
*   Cogs should import services and call service methods, keeping cogs strictly focused on interaction formatting and presentation.
*   Services should never interact directly with database engines; they must interact via Repositories.
