"""
Shared plotting palette — import this, never redefine colors inline in a
plotting script. One color per model, consistent across all figures.
"""

import zlib

# Extend as new models are added to experiments. Do not reuse a hex across
# two models that appear in the same figure set.
KNOWN_MODEL_COLORS = {
    "gemma3:12b": "#1b9e77",
    "gemma3:4b": "#66c2a5",
    "llama3.2:3b": "#d95f02",
    "llama3.1:8b": "#e6ab02",
    "qwen2.5:7b": "#7570b3",
    "phi4:14b": "#e7298a",
    "mistral:7b": "#66a61e",
}

# Deterministic fallback for models not yet in KNOWN_MODEL_COLORS, so a
# figure never crashes on an unregistered tag. Add the real mapping above
# once the model is in regular use.
FALLBACK_PALETTE = [
    "#a6761d", "#666666", "#1f78b4", "#b2182b",
    "#33a02c", "#6a3d9a", "#b15928", "#a6cee3",
]

CI_BAND_ALPHA = 0.2
T50_LINE_STYLE = {"color": "#333333", "linestyle": "--", "linewidth": 1}


def color_for_model(model: str) -> str:
    if model in KNOWN_MODEL_COLORS:
        return KNOWN_MODEL_COLORS[model]
    idx = zlib.crc32(model.encode()) % len(FALLBACK_PALETTE)
    return FALLBACK_PALETTE[idx]
