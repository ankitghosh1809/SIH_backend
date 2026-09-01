# app/schemas_explain.py — Round 3 (Agent P).
#
# Kept out of app/schemas.py deliberately: that file is the shared contract every
# Round-3 agent could in principle touch, and the work order scopes its one
# permitted change there to the new `uncertainty` field on PredictionField. This
# response shape is specific to the /explain endpoint, so it gets its own file
# instead of adding more surface area to the shared one.
from pydantic import BaseModel


class ExplainResponse(BaseModel):
    scan_id: str
    dr_uncertainty: float
    cataract_uncertainty: float
    explanation_text: str

    # FUTURE (Round 4 candidate, not built here): the work order's stretch goal
    # proposed an `agreement: bool` field on this response — does a
    # classical-only model agree with the hybrid-quantum model's call
    # (positive/negative) for this same scan? Building it is explicitly
    # conditional on confirming with Arushi & Pramati whether their pipeline
    # can produce both a classical and a hybrid-quantum prediction per live
    # image (vs. only offline, against the model_metrics benchmark test set)
    # — not something this branch could confirm on its own, so per the work
    # order's own instruction this is left as a documented future item
    # instead of a guessed-at field.
