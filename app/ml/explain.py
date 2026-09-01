"""
Explanation text generator for the /explain endpoint (Round 3 / Agent P).

Deliberately separate from app.ml.inference: this is presentation copy, not a
numeric adapter, so keeping it in its own file makes it obvious at a glance
that nothing here does real computation yet.
"""


def generate_explanation(dr_probability: float, cataract_probability: float) -> str:
    """PLACEHOLDER explanation text. Do not invent specific-sounding clinical claims (e.g. named
    retinal regions) — the current heatmap is a flat placeholder image with zero real spatial
    information, so any claim about *where* the model focused would be fabricated. Keep this
    honestly generic until Grad-CAM output is real."""
    return (
        "This explanation is running against the placeholder model. Once the real "
        "hybrid-quantum model is integrated, this will describe the specific retinal "
        "regions its Grad-CAM output highlights."
    )
