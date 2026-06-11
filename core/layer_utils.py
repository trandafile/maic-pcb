"""Shared layer-type classification.

The project JSON uses a mixed vocabulary for layer 'type' ("metal",
"dielectric", "copper", "core", "prepreg", "soldermask"...). Every engine
must classify metals the same way; use this helper instead of comparing
against a single literal.
"""


def is_metal_layer(layer) -> bool:
    """True when the layer's type denotes a metal (handles 'metal',
    'copper', 'copper foil')."""
    l_type = str(layer.get('type', '')).lower()
    return 'metal' in l_type or 'copper' in l_type
