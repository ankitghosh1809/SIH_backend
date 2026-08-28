"""
STUB — DELETE AT STITCH TIME.

Same caveat as database.py: this is a placeholder built to the contract Agent D
needs (get_latest_metrics()), not a verbatim copy of Agent C's stub, which wasn't
available in this sandbox. Replace with the real shared stub or Agent A's
implementation at stitch time.
"""

from typing import Optional, TypedDict


class _MetricsDict(TypedDict):
    classical: Optional[dict]
    hybrid_quantum: Optional[dict]
    evaluated_on: Optional[str]


def get_latest_metrics() -> _MetricsDict:
    """
    Real version (Agent A) queries the model_metrics table for the most recent
    'classical' and 'hybrid_quantum' rows and shapes them to match
    schemas.ModelMetrics. This stub returns "no data yet" so /api/v1/metrics can
    be built and tested before the real DB is wired up.
    """
    return {
        "classical": None,
        "hybrid_quantum": None,
        "evaluated_on": None,
    }
