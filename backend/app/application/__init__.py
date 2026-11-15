"""Application layer: use cases (services) and the ports they depend on.

Services depend only on abstractions declared in :mod:`app.application.ports`
and on the domain. Concrete adapters are wired in ``app/container.py``.
"""
