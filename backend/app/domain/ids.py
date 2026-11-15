"""Identity generation for entities.

Entities create their own ids (UUID4 hex) so they are complete before they
are persisted. This keeps the domain independent of database sequences and
lets in-memory fakes and SQL adapters behave identically.
"""

import uuid


def new_id() -> str:
    """Return a new globally unique entity id."""
    return uuid.uuid4().hex
