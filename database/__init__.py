"""Database package for NoSpaceFGK.

Exposes connection manager, schemas, migration runners, and seeder tools.
"""

from database.connection import DatabaseManager
from database.schema import MIGRATIONS
from database.seed import seed_database
