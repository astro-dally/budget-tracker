"""Domain layer: entities, value objects and pattern participants.

This package imports **only** the Python standard library. Frameworks
(FastAPI, SQLAlchemy, Pydantic) live in the outer layers, which depend on
this package and never the other way round (Dependency Inversion). The rule
is enforced automatically by ``tests/test_architecture.py``.
"""
