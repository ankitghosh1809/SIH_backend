"""
STUB — DELETE AT STITCH TIME.

Placeholder for Agent A's real app/db/database.py. Exists only so Agent D can
prove the startup wiring in main.py works before a real database module lands.

Note: the work order says to copy Agent C's stub verbatim here. That file wasn't
available to build against in this environment (only this work order document
was), so this is a fresh placeholder built to the same contract Agent D actually
needs (a callable init_db()) rather than a literal copy of Agent C's version.
Replace with the real shared stub or Agent A's implementation at stitch time —
the signature should already match, so nothing importing it needs to change.
"""


def init_db() -> None:
    """Real version (Agent A) creates tables via SQLAlchemy. No-op here."""
    pass
